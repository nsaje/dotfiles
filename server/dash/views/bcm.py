from decimal import Decimal
import json

from dash import models, constants, forms
from utils import statsd_helper, api_common, exc
from dash.views import helpers


class AccountCreditView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_credit_get')
    def get(self, request, account_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)
        return self._get_response(account.id)

    @statsd_helper.statsd_timer('dash.api', 'account_credit_put')
    def put(self, request, account_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)
        
        data['status'] = constants.CreditLineItemStatus.PENDING
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
        item.save()

        return self.create_api_response(item.instance.pk)

    def _prepare_item(self, item):
        allocated = item.get_allocated_amount()
        return {
            'id': item.pk,
            'created_by': str(item.created_by),
            'created_on': item.created_dt.date(),
            'start_date': item.start_date,
            'end_date': item.end_date,
            'is_signed': item.status == constants.CreditLineItemStatus.SIGNED,
            'license_fee': helpers.format_decimal_to_percent(item.license_fee) + '%',
            'total': item.amount,
            'allocated': allocated,
            'budgets': [
                { 'id': b.pk, 'amount': b.amount } for b in item.budgets.all()
            ],
            'available': item.amount - allocated,
        }

    def _get_response(self, account_id):
        credit_items = models.CreditLineItem.objects.filter(
            account_id=account_id,
        ).exclude(
            status=constants.CreditLineItemStatus.CANCELED
        ).prefetch_related('budgets').order_by('-created_dt')
        
        return self.create_api_response({
            'active': self._get_active_credit(account_id, credit_items),
            'past': self._get_past_credit(account_id, credit_items),
            'totals': self._get_credit_totals(account_id, credit_items),
        })


    def _get_active_credit(self, account_id, credit_items):
        return [
            self._prepare_item(item)
            for item in credit_items if not item.is_past()
        ]
    
    def _get_past_credit(self, account_id, credit_items):
        return [
            self._prepare_item(item)
            for item in credit_items if item.is_past()
        ]
    
    def _get_credit_totals(self, account_id, credit_items):
        total = sum(credit.amount for credit in credit_items)
        allocated = sum(
            credit.get_allocated_amount() for credit in credit_items if not credit.is_past()
        )
        past = sum(credit.amount for credit in credit_items if credit.is_past())
        return {
            'total': str(total),
            'allocated': str(allocated),
            'past': str(past),
            'available': str(total - allocated - past),
        }


class AccountCreditItemView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_credit_item_get')
    def get(self, request, account_id, credit_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        item = models.CreditLineItem.objects.get(account_id=account.id, pk=credit_id)
        return self._get_response(item)

    @statsd_helper.statsd_timer('dash.api', 'account_credit_item_delete')
    def delete(self, request, account_id, credit_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()
        
        account = helpers.get_account(request.user, account_id)

        item = models.CreditLineItem.objects.get(account_id=account.id, pk=credit_id)
        item.delete()
        return self.create_api_response()
    
    @statsd_helper.statsd_timer('dash.api', 'account_credit_item_post')
    def post(self, request, account_id, credit_id):
        if not request.user.has_perm('zemauth.account_credit_view'):
            raise exc.AuthorizationError()
        
        account = helpers.get_account(request.user, account_id)
        item = models.CreditLineItem.objects.get(account_id=account.id, pk=credit_id)
        request_data = json.loads(request.body)

        data = {}
        data.update(request_data)
        data['status'] = item.status

        if 'is_signed' in data:
            if data['is_signed']:
                data['status'] = constants.CreditLineItemStatus.SIGNED
            del data['is_signed']
        if 'license_fee' in data:
            data['license_fee'] = helpers.format_percent_to_decimal(data['license_fee'])
        item_form = forms.CreditLineItemForm(data, instance=item)

        if item_form.errors:
            raise exc.ValidationError(errors=item_form.errors)

        item_form.save()
        return self.create_api_response(credit_id)

    def _get_response(self, item):
        return self.create_api_response({
            'id': item.pk,
            'created_by': str(item.created_by or 'system'),
            'created_on': item.created_dt.date(),
            'start_date': item.start_date,
            'end_date': item.end_date,
            'is_signed': item.status == constants.CreditLineItemStatus.SIGNED,
            'license_fee': helpers.format_decimal_to_percent(item.license_fee) + '%',
            'amount': item.amount,
            'account_id': item.account_id,
            'comment': item.comment,
            'budgets': [
                {
                    'campaign': str(b.campaign),
                    'id': b.pk,
                    'total': b.amount,
                    'spend': b.get_spend_data(use_decimal=True)['total'],
                    'start_date': b.start_date,
                    'end_date': b.end_date,
                }
                for b in item.budgets.all().order_by('-created_dt')
            ],
        })


class CampaignBudgetView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_plus_get')
    def get(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_budget_view'):
            raise exc.AuthorizationError()
        campaign = helpers.get_campaign(request.user, campaign_id)
        return self._get_response(campaign)

    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_plus_put')
    def put(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_budget_view'):
            raise exc.AuthorizationError()
        campaign = helpers.get_campaign(request.user, campaign_id)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)

        data['campaign'] = campaign.id

        item = forms.BudgetLineItemForm(data)
        if item.errors:
            raise exc.ValidationError(errors=item.errors)

        item.instance.created_by = request.user
        item.save()
        
        return self.create_api_response(item.instance.pk)

    def _prepare_item(self, item):
        spend = item.get_spend_data(use_decimal=True)['total']
        return {
            'id': item.pk,
            'start_date': item.start_date,
            'end_date': item.end_date,
            'state': item.state(),
            'license_fee': helpers.format_decimal_to_percent(item.credit.license_fee) + '%',
            'total': item.amount,
            'spend': spend,
            'available': item.amount - spend,
            'is_editable': item.is_editable(),
            'is_updatable': item.is_updatable(),
            'comment': item.comment,
        }

    def _get_response(self, campaign):
        budget_items = models.BudgetLineItem.objects.filter(
            campaign_id=campaign.id,
        ).select_related('credit').order_by('-created_dt')
        return self.create_api_response({
            'active': self._get_active_budget(budget_items),
            'past': self._get_past_budget(budget_items),
            'totals': self._get_budget_totals(campaign),
            'credits': self._get_available_credit_items(campaign),
        })

    def _get_available_credit_items(self, campaign):
        available_credits = models.CreditLineItem.objects.filter(
            account=campaign.account
        )
        return [
            {
                'id': credit.pk,
                'total': credit.amount,
                'available': credit.amount - credit.get_allocated_amount(),
                'license_fee': helpers.format_decimal_to_percent(credit.license_fee),
                'start_date': credit.start_date,
                'end_date': credit.end_date,
                'is_available': credit.is_available()
            }
            for credit in available_credits
        ]

    def _get_active_budget(self, items):
        return [self._prepare_item(b) for b in items if b.state() in (
            constants.BudgetLineItemState.ACTIVE,
            constants.BudgetLineItemState.PENDING,
        )]
    
    def _get_past_budget(self, items):
        return [self._prepare_item(b) for b in items if b.state() in (
            constants.BudgetLineItemState.DEPLETED,
            constants.BudgetLineItemState.INACTIVE,
        )]
    
    def _get_budget_totals(self, campaign):
        data = {
            'current': {
                'available': Decimal('0.0000'),
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
        for item in models.CreditLineItem.objects.filter(account=campaign.account):
            allocated = item.get_allocated_amount()
            if item.status != constants.CreditLineItemStatus.SIGNED:
                continue
            data['current'][item.is_past() and 'past' or 'available'] += Decimal(item.amount)
            if not item.is_past():
                data['current']['unallocated'] += Decimal(item.amount - allocated)
            
        for item in models.BudgetLineItem.objects.filter(campaign_id=campaign.id):
            spend_data = item.get_spend_data(use_decimal=True)
            if item.state() in (constants.BudgetLineItemState.ACTIVE,
                                constants.BudgetLineItemState.PENDING):
                data['current']['available'] -= Decimal(spend_data['total'])
            else:
                data['current']['past'] -= Decimal(spend_data['total'])
            if item.state() == constants.BudgetLineItemState.PENDING:
                continue
            
            data['lifetime']['campaign_spend'] += spend_data['total']
            data['lifetime']['media_spend'] += spend_data['media']
            data['lifetime']['data_spend'] += spend_data['data']
            data['lifetime']['license_fee'] += spend_data['license_fee']
        return data


class CampaignBudgetItemView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_item_get')
    def get(self, request, campaign_id, budget_id):
        if not request.user.has_perm('zemauth.campaign_budget_view'):
            raise exc.AuthorizationError()
        item = models.BudgetLineItem.objects.get(
            campaign_id=campaign_id,
            pk=budget_id,
        )
        return self._get_response(item)

    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_item_post')
    def post(self, request, campaign_id, budget_id):
        if not request.user.has_perm('zemauth.campaign_budget_view'):
            raise exc.AuthorizationError()
        campaign = helpers.get_campaign(request.user, campaign_id)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)
        
        data['campaign'] = campaign.id

        item = forms.BudgetLineItemForm(
            data,
            instance=models.BudgetLineItem.objects.get(campaign_id=campaign_id, pk=budget_id)
        )
        
        if item.errors:
            raise exc.ValidationError(errors=item.errors)

        item.save()
        
        return self.create_api_response(item.instance.pk)

    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_item_delete')
    def delete(self, request, campaign_id, budget_id):
        if not request.user.has_perm('zemauth.campaign_budget_view'):
            raise exc.AuthorizationError()
        
        campaign = helpers.get_campaign(request.user, campaign_id)
        item = models.BudgetLineItem.objects.get(campaign_id=campaign.id, pk=budget_id)
        try:
            item.delete()
        except AssertionError:
            raise exc.ValidationError('Budget item is not pending')
        return self.create_api_response(True)

    def _get_response(self, item):
        return self.create_api_response({
            'amount': item.amount,
            'created_by': str(item.created_by),
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
        })
