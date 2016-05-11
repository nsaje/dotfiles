
from dash.views import helpers
from dash.views import breakdowns_helpers
from utils import exc
from utils import api_common

import stats.api

"""
SPEC:
- breakdown array includes base level
  all_accounts/breakdown/account
- everytime we include the params (this is the size for the last level):
  - page_size:
  - page:
- we include previous level ids

----------------------------------------------------
breakdown = [base_level, structure, delivery, time]
            [campaign, source, dma, day]

LVL_BASE
breakdown = [campaign]
account_id = X
page_size = 10
page = 1

LVL_1
breakdown [campaign, source]
account = X
campaign = [1, 2, 3]
page_size = 10  <-- how many sources per campaign
page = 1

LVL_2
breakdown [campaign, source, dma]
account = X
campaign = {
   1: [dmas]
   2: [dmas]
   3: [dmas]
}
page_size = 10
page = 1

LVL_3
breakdown [campaign, source, dma, day]
account = X
campaign = {
   1: [dmas]
   2: [dmas]
   3: [dmas]
}
page_size = 10 <-- days
page = 1

"""


class AllAccountsBreakdown(api_common.BaseApiView):
    def get(self, request, breakdown):
        return self.create_api_response({})


class AccountBreakdown(api_common.BaseApiView):
    # 1 account is broken by campaigns and other
    def get(self, request, account_id, breakdown):
        return self.post(request, account_id, breakdown)

    def post(self, request, account_id, breakdown):

        print account_id, breakdown


        account = helpers.get_account(request.user, account_id)

        constraints = breakdowns_helpers.clean_default_params(request)
        constraints['account'] = account
        breakdown = breakdowns_helpers.clean_breakdown(breakdown)
        breakdown_constraints = breakdowns_helpers.clean_breakdown_page(request, breakdown)

        page, page_size = breakdowns_helpers.clean_page_params(request)
        order = breakdowns_helpers.clean_order(request)

        print 'CONSTRAINTS', constraints
        print 'BREAKDOWN_CONSTRAINTS', breakdown_constraints

        print 'BREAKDOWN', breakdown
        print 'PAGE {} PAGESIZE {} ORDER {}'.format(page, page_size, order)

        if False:
            return self.create_api_response({
                'breakdown': breakdown,
                'page': page,
                'page_size': page_size,
            })

        report = stats.api.query_breakdown(
            request.user,
            breakdown,
            constraints,
            breakdown_constraints,
            order,
            page,
            page_size
        )

        return self.create_api_response(report)


class CampaignBreakdown(api_common.BaseApiView):
    def get(self, request, campaign_id, breakdown):
        return self.create_api_response({})


class AdGroupBreakdown(api_common.BaseApiView):
    def get(self, request, ad_group_id, breakdown):
        return self.create_api_response({})
