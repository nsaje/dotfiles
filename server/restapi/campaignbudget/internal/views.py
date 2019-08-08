import restapi.campaignbudget.v1.views

from . import serializers


class CampaignBudgetViewSet(restapi.campaignbudget.v1.views.CampaignBudgetViewSet):
    serializer = serializers.CampaignBudgetSerializer
