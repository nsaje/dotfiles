from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from django.conf import settings

from django.db.models import Q

from dash.api_common import BaseApiView
from dash import models


# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html', {'staticUrl': settings.CLIENT_STATIC_URL})


class NavigationDataView(BaseApiView):
    def get(self, request):
        user_id = request.user.id

        ad_groups = (
            models.AdGroup.objects
            .select_related('campaign__account')
            .filter(Q(campaign__users__in=[user_id]) | Q(campaign__account__users__in=[user_id]))
        )

        accounts = {}
        for ad_group in ad_groups:
            campaign = ad_group.campaign
            account = campaign.account

            if account.id not in accounts:
                accounts[account.id] = {
                    'id': account.id,
                    'name': account.name,
                    'campaigns': {}
                }

            campaigns = accounts[account.id]['campaigns']

            if campaign.id not in campaigns:
                campaigns[campaign.id] = {
                    'id': campaign.id,
                    'name': campaign.name,
                    'adGroups': []
                }

            campaigns[campaign.id]['adGroups'].append({'id': ad_group.id, 'name': ad_group.name})

        data = []
        for account in accounts.values():
            account['campaigns'] = account['campaigns'].values()
            data.append(account)

        return self.create_api_response(data)
