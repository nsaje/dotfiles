import rest_framework.permissions

import restapi.campaignbudget.v1.views

from . import serializers


class CampaignBudgetViewSet(restapi.campaignbudget.v1.views.CampaignBudgetViewSet):
    permission_classes = (rest_framework.permissions.IsAuthenticated,)
    serializer = serializers.CampaignBudgetSerializer
