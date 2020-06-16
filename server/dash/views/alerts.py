import dash.features.alerts
from dash.views import helpers
from utils import api_common


class AllAccountsAlerts(api_common.BaseApiView):
    def get(self, request):
        return self.create_api_response({"alerts": dash.features.alerts.get_accounts_alerts(request)})


class AccountAlerts(api_common.BaseApiView):
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        return self.create_api_response({"alerts": dash.features.alerts.get_account_alerts(request, account)})


class CampaignAlerts(api_common.BaseApiView):
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        return self.create_api_response({"alerts": dash.features.alerts.get_campaign_alerts(request, campaign)})


class AdGroupAlerts(api_common.BaseApiView):
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        return self.create_api_response(
            {"alerts": dash.features.alerts.get_campaign_alerts(request, ad_group.campaign)}
        )
