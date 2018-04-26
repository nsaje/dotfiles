from decimal import Decimal
import json
import logging

from django.forms.models import model_to_dict

from dash import models, constants, forms
from utils import api_common, exc
from dash.views import helpers
from automation import campaign_stop

import automation.campaignstop
import core.bcm
import core.bcm.bcm_slack
import core.multicurrency

logger = logging.getLogger(__name__)

EXCLUDE_ACCOUNTS_LOW_AMOUNT_CHECK = (
    431, 305
)


def _can_manage_agency_margin(user, campaign):
    return user.has_perm('zemauth.can_manage_agency_margin')


def _should_add_platform_costs(user, campaign):
    return not campaign.account.uses_bcm_v2 or\
        user.has_perm('zemauth.can_view_platform_cost_breakdown')


def _should_add_agency_costs(user, campaign):
    return (campaign.account.uses_bcm_v2 and user.has_perm('zemauth.can_view_agency_cost_breakdown')) or\
        (not campaign.account.uses_bcm_v2 and user.has_perm('zemauth.can_view_agency_margin'))


class AccountCreditView(api_common.BaseApiView):

    def get(self, request, account_id):
        if not self.rest_proxy and not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)
        return self._get_response(account)

    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        request_data = json.loads(request.body)
        response_data = {'canceled': []}
        account_credits_to_cancel = models.CreditLineItem.objects.filter_by_account(
            account).filter(pk__in=request_data['cancel'])

        for credit in account_credits_to_cancel:
            credit.cancel()
            response_data['canceled'].append(credit.pk)
        return self.create_api_response(response_data)

    def put(self, request, account_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)

        data['status'] = constants.CreditLineItemStatus.PENDING
        if 'is_agency' in data and data['is_agency'] and account.is_agency():
            data['agency'] = account.agency_id
        else:
            data['account'] = account.id

        if 'is_signed' in data:
            if data['is_signed']:
                data['status'] = constants.CreditLineItemStatus.SIGNED
            del data['is_signed']
        if 'license_fee' in data:
            data['license_fee'] = helpers.format_percent_to_decimal(data['license_fee'])

        data['currency'] = account.currency

        item = forms.CreditLineItemForm(data)

        if item.errors:
            raise exc.ValidationError(errors=item.errors)

        item.instance.created_by = request.user
        item.save(request=request, action_type=constants.HistoryActionType.CREATE)
        core.bcm.bcm_slack.log_to_slack(account_id, core.bcm.bcm_slack.SLACK_NEW_CREDIT_MSG.format(
            credit_id=item.instance.pk,
            url=core.bcm.bcm_slack.ACCOUNT_URL.format(account_id),
            account_id=account_id,
            account_name=account.get_long_name(),
            amount=item.instance.amount,
            currency_symbol=core.multicurrency.get_currency_symbol(item.instance.currency),
            end_date=item.instance.end_date
        ))
        return self.create_api_response(item.instance.pk)

    def _prepare_credit(self, credit):
        flat_fee = credit.get_flat_fee_on_date_range(credit.start_date, credit.end_date)
        allocated = credit.get_allocated_amount()
        return {
            'id': credit.pk,
            'created_by': str(credit.created_by or 'Zemanta One'),
            'created_on': credit.created_dt.date(),
            'start_date': credit.start_date,
            'end_date': credit.end_date,
            'currency': credit.currency,
            'is_signed': credit.status == constants.CreditLineItemStatus.SIGNED,
            'is_canceled': credit.status == constants.CreditLineItemStatus.CANCELED,
            'license_fee': helpers.format_decimal_to_percent(credit.license_fee) + '%',
            'flat_fee': flat_fee,
            'total': credit.effective_amount(),
            'allocated': allocated,
            'comment': credit.comment,
            'salesforce_url': credit.get_salesforce_url(),
            'is_agency': credit.is_agency(),
            'budgets': [
                {'id': b.pk, 'amount': b.amount} for b in credit.budgets.all()
            ],
            'available': credit.effective_amount() - allocated,
        }

    def _get_response(self, account):
        credit_items = models.CreditLineItem.objects.filter_by_account(account)
        credit_items = credit_items.prefetch_related('budgets').order_by('-start_date', '-end_date', '-created_dt')

        return self.create_api_response({
            'active': self._get_active_credit(credit_items),
            'past': self._get_past_credit(credit_items),
            'totals': self._get_credit_totals(credit_items, account),
        })

    def _get_active_credit(self, credit_items):
        return [
            self._prepare_credit(item)
            for item in credit_items if not item.is_past()
        ]

    def _get_past_credit(self, credit_items):
        return [
            self._prepare_credit(item)
            for item in credit_items if item.is_past()
        ]

    def _get_credit_totals(self, credit_items, account):
        valid_credit_items = [credit for credit in credit_items if credit.status !=
                              constants.CreditLineItemStatus.PENDING]
        total = sum(credit.effective_amount() for credit in valid_credit_items)
        allocated = sum(
            credit.get_allocated_amount() for credit in valid_credit_items if not credit.is_past()
        )
        past = sum(credit.effective_amount() for credit in valid_credit_items if credit.is_past())
        return {
            'total': str(total),
            'allocated': str(allocated),
            'past': str(past),
            'available': str(total - allocated - past),
            'currency': account.currency,
        }


class AccountCreditItemView(api_common.BaseApiView):

    def get(self, request, account_id, credit_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        item = models.CreditLineItem.objects.filter_by_account(account).get(pk=credit_id)
        return self._get_response(account, item)

    def delete(self, request, account_id, credit_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)

        item = models.CreditLineItem.objects.filter_by_account(account).get(pk=credit_id)
        item.delete()

        account.write_history(
            'Deleted credit',
            action_type=constants.HistoryActionType.CREDIT_CHANGE,
            user=request.user
        )
        return self.create_api_response()

    def post(self, request, account_id, credit_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        item = models.CreditLineItem.objects.filter_by_account(account).get(pk=credit_id)
        request_data = json.loads(request.body)

        data = {}
        data.update(request_data)
        data['status'] = item.status

        if 'is_agency' in data and data['is_agency'] and account.is_agency():
            data['account'] = None
            data['agency'] = account.agency_id
        else:
            data['account'] = account.id
            data['agency'] = None
        if 'is_signed' in data:
            if data['is_signed']:
                data['status'] = constants.CreditLineItemStatus.SIGNED
            del data['is_signed']
        if 'license_fee' in data:
            data['license_fee'] = helpers.format_percent_to_decimal(data['license_fee'])
        item_form = forms.CreditLineItemForm(data, instance=item)

        if item_form.errors:
            raise exc.ValidationError(errors=item_form.errors)

        item_form.save(request=request, action_type=constants.HistoryActionType.CREDIT_CHANGE)
        changes = item_form.instance.get_model_state_changes(model_to_dict(item_form.instance))
        core.bcm.bcm_slack.log_to_slack(account_id, core.bcm.bcm_slack.SLACK_UPDATED_CREDIT_MSG.format(
            credit_id=credit_id,
            url=core.bcm.bcm_slack.ACCOUNT_URL.format(account_id),
            account_id=account_id,
            account_name=account.get_long_name(),
            history=item_form.instance.get_history_changes_text(changes),
        ))
        return self.create_api_response(credit_id)

    def _get_response(self, account, item):
        return self.create_api_response({
            'id': item.pk,
            'created_by': str(item.created_by or 'Zemanta One'),
            'created_on': item.created_dt.date(),
            'start_date': item.start_date,
            'end_date': item.end_date,
            'currency': item.currency,
            'is_signed': item.status == constants.CreditLineItemStatus.SIGNED,
            'is_canceled': item.status == constants.CreditLineItemStatus.CANCELED,
            'license_fee': helpers.format_decimal_to_percent(item.license_fee) + '%',
            'amount': item.amount,
            'account_id': account.id,
            'comment': item.comment,
            'is_agency': item.is_agency(),
            'salesforce_url': item.get_salesforce_url(),
            'budgets': [
                {
                    'campaign': str(b.campaign),
                    'id': b.pk,
                    'total': b.allocated_amount(),
                    'spend': (
                        b.get_spend_data()['etfm_total'] if account.uses_bcm_v2
                        else b.get_spend_data()['etf_total']
                    ),
                    'start_date': b.start_date,
                    'end_date': b.end_date,
                    'currency': item.currency,
                    'comment': b.comment
                }
                for b in item.budgets.all().order_by('-created_dt')[:100]
            ],
        })


class CampaignBudgetView(api_common.BaseApiView):

    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id, select_related=True)
        return self._get_response(request.user, campaign)

    def put(self, request, campaign_id):
        if request.user.has_perm('zemauth.disable_budget_management'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id, select_related=True)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)

        data['campaign'] = campaign.id
        if 'margin' in data:
            if not _can_manage_agency_margin(request.user, campaign):
                del data['margin']
            else:
                data['margin'] = helpers.format_percent_to_decimal(data['margin'] or '0')

        form = forms.BudgetLineItemForm(data)
        if form.errors:
            raise exc.ValidationError(errors=form.errors)

        item = core.bcm.BudgetLineItem.objects.create(
            request=request,
            campaign=campaign,
            credit=form.cleaned_data['credit'],
            start_date=form.cleaned_data['start_date'],
            end_date=form.cleaned_data['end_date'],
            amount=form.cleaned_data['amount'],
            margin=form.cleaned_data['margin'],
            comment=form.cleaned_data['comment']
        )

        return self.create_api_response(item.pk)

    def _prepare_item(self, user, campaign, item):
        if user.has_perm('zemauth.can_manage_budgets_in_local_currency'):
            spend_data = item.get_local_spend_data()
        else:
            spend_data = item.get_spend_data()

        if campaign.account.uses_bcm_v2:
            spend = spend_data['etfm_total']
        else:
            spend = spend_data['etf_total']

        allocated = item.allocated_amount()
        result = {
            'id': item.pk,
            'start_date': item.start_date,
            'credit': item.credit.id,  # FIXME(nsaje) hack to return credit id in REST API
            'end_date': item.end_date,
            'state': item.state(),
            'currency': item.credit.currency if user.has_perm('zemauth.can_manage_budgets_in_local_currency') else constants.Currency.USD,
            'total': allocated,
            'spend': spend,
            'available': allocated - spend,
            'is_editable': item.is_editable(),
            'is_updatable': item.is_updatable(),
            'comment': item.comment,
        }

        if _should_add_platform_costs(user, campaign):
            result['license_fee'] = helpers.format_decimal_to_percent(item.credit.license_fee) + '%'

        if _should_add_agency_costs(user, campaign):
            result['margin'] = helpers.format_decimal_to_percent(item.margin) + '%'

        return result

    def _get_response(self, user, campaign):
        currency = constants.Currency.USD
        if user.has_perm('zemauth.can_manage_budgets_in_local_currency'):
            currency = campaign.account.currency

        budget_items = models.BudgetLineItem.objects.filter(
            campaign_id=campaign.id,
        ).select_related('credit').order_by('-created_dt').annotate_spend_data()
        credit_items = (models.CreditLineItem.objects
                        .filter_by_account(campaign.account)
                        .filter(currency=currency)
                        .prefetch_related('budgets'))

        active_budget = self._get_active_budget(user, campaign, budget_items)
        automatic_campaign_stop = campaign.get_current_settings().automatic_campaign_stop
        return self.create_api_response({
            'active': active_budget,
            'past': self._get_past_budget(user, campaign, budget_items),
            'totals': self._get_budget_totals(user, campaign, active_budget, budget_items, credit_items),
            'credits': self._get_available_credit_items(user, campaign, credit_items),
            'min_amount': (automatic_campaign_stop and
                           campaign_stop.get_min_budget_increase(campaign) or "0"),
        })

    def _get_available_credit_items(self, user, campaign, available_credits):
        credits = []
        for credit in available_credits:
            credit_dict = {
                'id': credit.pk,
                'total': credit.effective_amount(),
                'available': credit.effective_amount() - credit.get_allocated_amount(),
                'start_date': credit.start_date,
                'end_date': credit.end_date,
                'currency': credit.currency if user.has_perm('zemauth.can_manage_budgets_in_local_currency') else constants.Currency.USD,
                'comment': credit.comment,
                'is_available': credit.is_available(),
                'is_agency': credit.is_agency(),
            }

            if _should_add_platform_costs(user, campaign):
                credit_dict['license_fee'] = helpers.format_decimal_to_percent(credit.license_fee)
            credits.append(credit_dict)

        return credits

    def _get_active_budget(self, user, campaign, items):
        return [self._prepare_item(user, campaign, b) for b in items if b.state() in (
            constants.BudgetLineItemState.ACTIVE,
            constants.BudgetLineItemState.PENDING,
        )]

    def _get_past_budget(self, user, campaign, items):
        return [self._prepare_item(user, campaign, b) for b in items if b.state() in (
            constants.BudgetLineItemState.DEPLETED,
            constants.BudgetLineItemState.INACTIVE,
        )]

    def _get_budget_totals(self, user, campaign, active_budget, budget_items, credits):
        data = {
            'current': {
                'available': sum([x['available'] for x in active_budget]),
                'unallocated': Decimal('0.0000'),
                'past': Decimal('0.0000'),
            },
            'lifetime': {
                'campaign_spend': Decimal('0.0000'),
            },
            'currency': campaign.account.currency if user.has_perm('zemauth.can_manage_budgets_in_local_currency') else constants.Currency.USD,
        }

        if _should_add_platform_costs(user, campaign):
            data['lifetime']['media_spend'] = Decimal('0.0000')
            data['lifetime']['data_spend'] = Decimal('0.0000')
            data['lifetime']['license_fee'] = Decimal('0.0000')

        if _should_add_agency_costs(user, campaign):
            data['lifetime']['margin'] = Decimal('0.0000')

        for item in credits:
            if item.status != constants.CreditLineItemStatus.SIGNED or item.is_past():
                continue
            data['current']['unallocated'] += Decimal(item.amount - item.flat_fee() - item.get_allocated_amount())

        for item in budget_items:
            if item.state() == constants.BudgetLineItemState.PENDING:
                continue

            if user.has_perm('zemauth.can_manage_budgets_in_local_currency'):
                spend_data = item.get_local_spend_data()
            else:
                spend_data = item.get_spend_data()

            if campaign.account.uses_bcm_v2:
                data['lifetime']['campaign_spend'] += spend_data['etfm_total']
            else:
                data['lifetime']['campaign_spend'] += spend_data['etf_total']

            if _should_add_platform_costs(user, campaign):
                data['lifetime']['media_spend'] += spend_data['media']
                data['lifetime']['data_spend'] += spend_data['data']
                data['lifetime']['license_fee'] += spend_data['license_fee']

            if _should_add_agency_costs(user, campaign):
                data['lifetime']['margin'] += spend_data['margin']

        return data


class CampaignBudgetItemView(api_common.BaseApiView):

    def get(self, request, campaign_id, budget_id):
        helpers.get_campaign(request.user, campaign_id, select_related=True)
        try:
            item = models.BudgetLineItem.objects.get(
                campaign_id=campaign_id,
                pk=budget_id,
            )
        except models.BudgetLineItem.DoesNotExist:
            raise exc.MissingDataError('Budget does not exist!')
        return self._get_response(request.user, item)

    def post(self, request, campaign_id, budget_id):
        if request.user.has_perm('zemauth.disable_budget_management'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id, select_related=True)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)
        if 'margin' in data:
            if not _can_manage_agency_margin(request.user, campaign):
                del data['margin']
            else:
                data['margin'] = helpers.format_percent_to_decimal(data['margin'] or '0')

        data['campaign'] = campaign.id

        instance = models.BudgetLineItem.objects.get(campaign_id=campaign_id, pk=budget_id)
        item = forms.BudgetLineItemForm(
            data,
            instance=instance
        )

        self._validate_amount(data, item)

        if item.errors:
            raise exc.ValidationError(errors=item.errors)

        item.save(request=request, action_type=constants.HistoryActionType.BUDGET_CHANGE)
        state_changed = campaign_stop.perform_landing_mode_check(
            campaign,
            campaign.get_current_settings()
        )

        changes = item.instance.get_model_state_changes(model_to_dict(item.instance))
        core.bcm.bcm_slack.log_to_slack(campaign.account_id, core.bcm.bcm_slack.SLACK_UPDATED_BUDGET_MSG.format(
            budget_id=budget_id,
            url=core.bcm.bcm_slack.CAMPAIGN_URL.format(campaign_id),
            campaign_id=campaign_id,
            campaign_name=campaign.get_long_name(),
            history=item.instance.get_history_changes_text(changes),
        ))
        return self.create_api_response({
            'id': item.instance.pk,
            'state_changed': state_changed,
        })

    def delete(self, request, campaign_id, budget_id):
        if request.user.has_perm('zemauth.disable_budget_management'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        item = models.BudgetLineItem.objects.get(campaign_id=campaign.id, pk=budget_id)
        try:
            item.delete()
        except AssertionError:
            raise exc.ValidationError('Budget item is not pending')
        campaign_stop.perform_landing_mode_check(campaign, campaign.get_current_settings())
        campaign.write_history(
            'Deleted budget',
            action_type=constants.HistoryActionType.BUDGET_CHANGE,
            user=request.user)
        return self.create_api_response(True)

    def _validate_amount(self, data, item):
        """
        Even if we run the campaign stop script every time the budget amount is lowered
        and stop the campaign 'immediately', overspend is still possible because the campaign
        will actually stop on external sources at the end of their local day.

        Because of this we define a 'budget minimum':
        budget_minimum = budget_spend + sum(daily_budgets) - overall_available_campaign_budget
        """
        prev_amount = item.instance.amount
        amount = Decimal(data.get('amount', '0'))
        if amount >= prev_amount:
            return
        if item.instance.campaign.real_time_campaign_stop:
            try:
                automation.campaignstop.validate_minimum_budget_amount(item.instance, amount)
            except automation.campaignstop.CampaignStopValidationException as e:
                item.errors.setdefault('amount', []).append(
                    'Budget amount has to be at least {currency_symbol}{min_amount:.2f}.'.format(
                        currency_symbol=core.multicurrency.get_currency_symbol(item.instance.credit.currency),
                        min_amount=e.min_amount,
                    ),
                )
        else:
            acc_id = item.instance.campaign.account_id
            if amount < prev_amount and acc_id not in EXCLUDE_ACCOUNTS_LOW_AMOUNT_CHECK:
                item.errors.setdefault('amount', []).append(
                    'If campaign stop is disabled amount cannot be lowered.'
                )
                return

    def _get_response(self, user, item):
        if user.has_perm('zemauth.can_manage_budgets_in_local_currency'):
            spend_data = item.get_local_spend_data()
        else:
            spend_data = item.get_spend_data()

        if item.campaign.account.uses_bcm_v2:
            spend = spend_data['etfm_total']
        else:
            spend = spend_data['etf_total']
        allocated = item.allocated_amount()
        response = {
            'id': item.id,
            'amount': item.amount,
            'spend': spend,
            'available': allocated - spend,
            'created_by': str(item.created_by or 'Zemanta One'),
            'created_at': item.created_dt,
            'start_date': item.start_date,
            'end_date': item.end_date,
            'comment': item.comment,
            'is_editable': item.is_editable(),
            'is_updatable': item.is_updatable(),
            'state': item.state(),
            'currency': item.credit.currency,
            'credit': {
                'id': item.credit.pk,
                'name': str(item.credit),
                'license_fee': item.credit.license_fee,
            }
        }
        if user.has_perm('zemauth.can_view_agency_margin'):
            response['margin'] = helpers.format_decimal_to_percent(item.margin) + '%'
        return self.create_api_response(response)
