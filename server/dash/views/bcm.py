from decimal import Decimal
import json

from dash import models, constants, forms
from utils import api_common, exc
from dash.views import helpers
from automation import campaign_stop

EXCLUDE_ACCOUNTS_LOW_AMOUNT_CHECK = (
    431, 305
)


class AccountCreditView(api_common.BaseApiView):

    def get(self, request, account_id):
        if not self.rest_proxy and not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)
        return self._get_response(account.id, account.agency)

    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        request_data = json.loads(request.body)
        response_data = {'canceled': []}
        account_credits_to_cancel = models.CreditLineItem.objects.filter(
            account_id=account_id, pk__in=request_data['cancel']
        )
        if account.agency is not None:
            account_credits_to_cancel |= models.CreditLineItem.objects.filter(
                agency=account.agency, pk__in=request_data['cancel']
            )

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

        item = forms.CreditLineItemForm(data)

        if item.errors:
            raise exc.ValidationError(errors=item.errors)

        item.instance.created_by = request.user
        item.save(request=request, action_type=constants.HistoryActionType.CREATE)

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
            'is_signed': credit.status == constants.CreditLineItemStatus.SIGNED,
            'is_canceled': credit.status == constants.CreditLineItemStatus.CANCELED,
            'license_fee': helpers.format_decimal_to_percent(credit.license_fee) + '%',
            'flat_fee': flat_fee,
            'total': credit.effective_amount(),
            'allocated': allocated,
            'comment': credit.comment,
            'is_agency': credit.is_agency(),
            'budgets': [
                {'id': b.pk, 'amount': b.amount} for b in credit.budgets.all()
            ],
            'available': credit.effective_amount() - allocated,
        }

    def _get_response(self, account_id, agency):
        credit_items = models.CreditLineItem.objects.filter(
            account_id=account_id
        ).prefetch_related('budgets').order_by('-start_date', '-end_date', '-created_dt')

        if agency is not None:
            credit_items |= models.CreditLineItem.objects.filter(
                agency=agency
            ).prefetch_related('budgets').order_by('-start_date', '-end_date', '-created_dt')

        return self.create_api_response({
            'active': self._get_active_credit(account_id, credit_items),
            'past': self._get_past_credit(account_id, credit_items),
            'totals': self._get_credit_totals(account_id, credit_items),
        })

    def _get_active_credit(self, account_id, credit_items):
        return [
            self._prepare_credit(item)
            for item in credit_items if not item.is_past()
        ]

    def _get_past_credit(self, account_id, credit_items):
        return [
            self._prepare_credit(item)
            for item in credit_items if item.is_past()
        ]

    def _get_credit_totals(self, account_id, credit_items):
        valid_credit_items = [credit for credit in credit_items if credit.status != constants.CreditLineItemStatus.PENDING]
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
        }


class AccountCreditItemView(api_common.BaseApiView):

    def get(self, request, account_id, credit_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        item = models.CreditLineItem.objects.filter(account_id=account.id, pk=credit_id).first()
        if item is None:
            item = models.CreditLineItem.objects.get(agency=account.agency, pk=credit_id)
        return self._get_response(account.id, item)

    def delete(self, request, account_id, credit_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)

        item = models.CreditLineItem.objects.filter(account_id=account.id, pk=credit_id).first()
        if item is None:
            item = models.CreditLineItem.objects.get(agency=account.agency, pk=credit_id)
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
        item = models.CreditLineItem.objects.filter(account_id=account.id, pk=credit_id).first()
        if item is None:
            item = models.CreditLineItem.objects.get(agency=account.agency, pk=credit_id)
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
        return self.create_api_response(credit_id)

    def _get_response(self, account_id, item):
        return self.create_api_response({
            'id': item.pk,
            'created_by': str(item.created_by or 'Zemanta One'),
            'created_on': item.created_dt.date(),
            'start_date': item.start_date,
            'end_date': item.end_date,
            'is_signed': item.status == constants.CreditLineItemStatus.SIGNED,
            'is_canceled': item.status == constants.CreditLineItemStatus.CANCELED,
            'license_fee': helpers.format_decimal_to_percent(item.license_fee) + '%',
            'amount': item.amount,
            'account_id': account_id,
            'comment': item.comment,
            'is_agency': item.is_agency(),
            'budgets': [
                {
                    'campaign': str(b.campaign),
                    'id': b.pk,
                    'total': b.allocated_amount(),
                    'spend': b.get_spend_data(use_decimal=True)['total'],
                    'start_date': b.start_date,
                    'end_date': b.end_date,
                    'comment': b.comment
                }
                for b in item.budgets.all().order_by('-created_dt')
            ],
        })


class CampaignBudgetView(api_common.BaseApiView):

    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        return self._get_response(request.user, campaign)

    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)

        data['campaign'] = campaign.id
        if 'margin' in data:
            if not request.user.has_perm('zemauth.can_manage_agency_margin'):
                del data['margin']
            else:
                data['margin'] = helpers.format_percent_to_decimal(data['margin'] or '0')

        item = forms.BudgetLineItemForm(data)
        if item.errors:
            raise exc.ValidationError(errors=item.errors)

        item.instance.created_by = request.user
        item.save(request=request, action_type=constants.HistoryActionType.CREATE)
        campaign_stop.perform_landing_mode_check(campaign, campaign.get_current_settings())

        return self.create_api_response(item.instance.pk)

    def _prepare_item(self, user, item):
        spend = item.get_spend_data(use_decimal=True)['total']
        allocated = item.allocated_amount()
        result = {
            'id': item.pk,
            'start_date': item.start_date,
            'end_date': item.end_date,
            'state': item.state(),
            'license_fee': helpers.format_decimal_to_percent(item.credit.license_fee) + '%',
            'total': allocated,
            'spend': spend,
            'available': allocated - spend,
            'is_editable': item.is_editable(),
            'is_updatable': item.is_updatable(),
            'comment': item.comment,
        }
        if user.has_perm('zemauth.can_view_agency_margin'):
            result['margin'] = helpers.format_decimal_to_percent(item.margin) + '%'
        return result

    def _get_response(self, user, campaign):
        budget_items = models.BudgetLineItem.objects.filter(
            campaign_id=campaign.id,
        ).select_related('credit').order_by('-created_dt')
        active_budget = self._get_active_budget(user, budget_items)
        automatic_campaign_stop = campaign.get_current_settings().automatic_campaign_stop
        return self.create_api_response({
            'active': active_budget,
            'past': self._get_past_budget(user, budget_items),
            'totals': self._get_budget_totals(user, campaign, active_budget),
            'credits': self._get_available_credit_items(user, campaign),
            'min_amount': (automatic_campaign_stop and
                           campaign_stop.get_min_budget_increase(campaign) or "0"),
        })

    def _get_available_credit_items(self, user, campaign):
        available_credits = models.CreditLineItem.objects.filter(
            account=campaign.account
        )

        agency = campaign.account.agency
        if agency is not None:
            available_credits |= models.CreditLineItem.objects.filter(
                agency=agency
            )

        return [
            {
                'id': credit.pk,
                'total': credit.effective_amount(),
                'available': credit.effective_amount() - credit.get_allocated_amount(),
                'license_fee': helpers.format_decimal_to_percent(credit.license_fee),
                'start_date': credit.start_date,
                'end_date': credit.end_date,
                'comment': credit.comment,
                'is_available': credit.is_available(),
                'is_agency': credit.is_agency(),
            }
            for credit in available_credits
        ]

    def _get_active_budget(self, user, items):
        return [self._prepare_item(user, b) for b in items if b.state() in (
            constants.BudgetLineItemState.ACTIVE,
            constants.BudgetLineItemState.PENDING,
        )]

    def _get_past_budget(self, user, items):
        return [self._prepare_item(user, b) for b in items if b.state() in (
            constants.BudgetLineItemState.DEPLETED,
            constants.BudgetLineItemState.INACTIVE,
        )]

    def _get_budget_totals(self, user, campaign, active_budget):
        data = {
            'current': {
                'available': sum([x['available'] for x in active_budget]),
                'unallocated': Decimal('0.0000'),
                'past': Decimal('0.0000'),
            },
            'lifetime': {
                'campaign_spend': Decimal('0.0000'),
                'media_spend': Decimal('0.0000'),
                'data_spend': Decimal('0.0000'),
                'license_fee': Decimal('0.0000'),
            }
        }

        if user.has_perm('zemauth.can_view_agency_margin'):
            data['lifetime']['margin'] = Decimal('0.0000')

        credits = models.CreditLineItem.objects.filter(account=campaign.account)

        agency = campaign.account.agency
        if agency is not None:
            credits |= models.CreditLineItem.objects.filter(agency=campaign.account.agency)

        for item in credits:
            if item.status != constants.CreditLineItemStatus.SIGNED or item.is_past():
                continue
            data['current']['unallocated'] += Decimal(item.amount - item.flat_fee() - item.get_allocated_amount())

        for item in models.BudgetLineItem.objects.filter(campaign_id=campaign.id):
            if item.state() == constants.BudgetLineItemState.PENDING:
                continue

            spend_data = item.get_spend_data(use_decimal=True)
            data['lifetime']['campaign_spend'] += spend_data['total']
            data['lifetime']['media_spend'] += spend_data['media']
            data['lifetime']['data_spend'] += spend_data['data']
            data['lifetime']['license_fee'] += spend_data['license_fee']
            if user.has_perm('zemauth.can_view_agency_margin'):
                data['lifetime']['margin'] += spend_data['margin']
        return data


class CampaignBudgetItemView(api_common.BaseApiView):

    def get(self, request, campaign_id, budget_id):
        helpers.get_campaign(request.user, campaign_id)
        try:
            item = models.BudgetLineItem.objects.get(
                campaign_id=campaign_id,
                pk=budget_id,
            )
        except models.BudgetLineItem.DoesNotExist:
            raise exc.MissingDataError('Budget does not exist!')
        return self._get_response(request.user, item)

    def post(self, request, campaign_id, budget_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)
        if 'margin' in data:
            if not request.user.has_perm('zemauth.can_manage_agency_margin'):
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

        return self.create_api_response({
            'id': item.instance.pk,
            'state_changed': state_changed,
        })

    def delete(self, request, campaign_id, budget_id):
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
        if not item.instance.campaign.get_current_settings().automatic_campaign_stop:
            acc_id = item.instance.campaign.account_id
            if amount < prev_amount and acc_id not in EXCLUDE_ACCOUNTS_LOW_AMOUNT_CHECK:
                item.errors.setdefault('amount', []).append(
                    'If automatic campaign stop is off amount cannot be lowered.'
                )
                return

        min_amount = campaign_stop.get_minimum_budget_amount(item.instance)
        if min_amount is None:
            return

        if min_amount > amount:
            item.errors.setdefault('amount', []).append(
                'Budget amount has to be at least ${}.'.format(
                    Decimal(min_amount).quantize(Decimal('1.00'))
                )
            )
        if not campaign_stop.is_current_time_valid_for_amount_editing(item.instance.campaign):
            item.errors.setdefault('amount', []).append(
                'You can lower the amount on an active budget line item after 12:00 UTC.'
            )

    def _get_response(self, user, item):
        spend = item.get_spend_data(use_decimal=True)['total']
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
            'credit': {
                'id': item.credit.pk,
                'name': str(item.credit),
                'license_fee': item.credit.license_fee,
            }
        }
        if user.has_perm('zemauth.can_view_agency_margin'):
            response['margin'] = helpers.format_decimal_to_percent(item.margin) + '%'
        return self.create_api_response(response)
