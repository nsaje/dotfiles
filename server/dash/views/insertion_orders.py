import json

from dash import models, constants, forms
from utils import statsd_helper, api_common, exc
from dash.views import helpers

class AccountCreditView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_credit_get')
    def get(self, request, account_id):
        return self._get_response(account_id)

    @statsd_helper.statsd_timer('dash.api', 'account_credit_put')
    def put(self, request, account_id):
        data = json.loads(request.body)
        data['status'] = constants.CreditLineItemStatus.PENDING
        data['account'] = account_id
        data['license_fee'] = helpers.format_percent_to_decimal(data['license_fee'])
        errors = {}

        item = forms.NewCreditLineItemForm(data)
        
        errors.update(item.errors)

        if errors:
            raise exc.ValidationError(errors=errors)

        item.instance.created_by = request.user
        item.save()
        
        return self._get_response(account_id)

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
            'available': item.amount - allocated,
        }

    def _get_response(self, account_id):
        credit_items = models.CreditLineItem.objects.filter(
            account_id=account_id,
        ).exclude(
            status=constants.CreditLineItemStatus.CANCELED
        ).prefetch_related('budgets')
        
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
        allocated = sum(credit.get_allocated_amount() for credit in credit_items)
        return {
            'total': str(total),
            'allocated': str(allocated),
            'available': str(total - allocated),
        }


class AccountCreditItemView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_credit_item_get')
    def get(self, request, account_id, credit_id):
        item = models.CreditLineItem.objects.get(account_id=account_id, pk=credit_id)
        return self._get_response(item)

    @statsd_helper.statsd_timer('dash.api', 'account_credit_item_delete')
    def delete(self, request, account_id, credit_id):
        item = models.CreditLineItem.objects.get(account_id=account_id, pk=credit_id)
        item.delete()
        return self.create_api_response(True)
    

    @statsd_helper.statsd_timer('dash.api', 'account_credit_item_pust')
    def post(self, request, account_id, credit_id):
        item = models.CreditLineItem.objects.get(account_id=account_id, pk=credit_id)
        data = json.loads(request.body)
        item.end_date = data['end_date']
        item_form = forms.CreditLineItemForm(instance=item)

        errors = {}
        errors.update(item_form.errors)

        if errors:
            raise exc.ValidationError(errors=errors)

        #item.save(Form)
        
        return self._get_response(item)

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
            'comment': item.comment,
            'budgets': [
                
            ],
        })


class CampaignBudgetView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_plus_get')
    def get(self, request, campaign_id):
        return self._get_response(campaign_id)

    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_plus_put')
    def put(self, request, campaign_id):
        data = json.loads(request.body)
        
        # TODO: create item
        return self._get_response(campaign_id)

    def _get_response(self, campaign_id):
        return self.create_api_response({
            'active': self._get_active_credit(budget_id, budget_items),
            'past': self._get_past_credit(budget_id, budget_items),
            'totals': self._get_credit_totals(budget_id, budget_items),
        })

    def _get_active_budget(self, budget_id):
        return []
    
    def _get_past_budget(self, budget_id):
        return []
    
    def _get_budget_totals(self, budget_id):
        # TODO: calculate totals
        return {
            'current': {
                'available': '0',
                'unallocated': '0',
            },
            'lifetime': {
                'campaign_spend': '0',
                'media_spend': '0',
                'data_spend': '0',
                'license_fee': '0',
            }
        }


class CampaignBudgetItemView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_item_get')
    def get(self, request, campaign_id):
        pass

    @statsd_helper.statsd_timer('dash.api', 'campaign_budget_item_post')
    def post(self, request, campaign_id):
        pass
