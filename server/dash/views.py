import datetime
import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from dash import api_common
from dash import exc
from dash import forms
from dash import models

import constants

from django.db.models import Q

from dash.api_common import BaseApiView
from dash import models


# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html', {'staticUrl': settings.CLIENT_STATIC_URL})


class User(BaseApiView):
    def get(self, request, user_id):
        response = {}

        if user_id == 'current':
            response['user'] = self.get_dict(request.user)

        return self.create_api_response(response)

    def get_dict(self, user):
        result = {}

        if user:
            result = {
                'id': str(user.pk),
                'email': user.email,
            }

        return result


class NavigationDataView(BaseApiView):
    def get(self, request):
        user_id = request.user.id

        if request.user.is_superuser:
            ad_groups = models.AdGroup.objects.\
                select_related('campaign__account').\
                all()

        else:
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


class AdGroupSettings(api_common.BaseApiView):
    def get(self, request, ad_group_id):
        try:
            ad_group = models.AdGroup.user_objects.get_for_user(request.user).\
                filter(id=int(ad_group_id)).get()
        except models.AdGroup.DoesNotExist:
            raise exc.MissingDataError('Ad Group does not exist')

        settings = self.get_current_settings(ad_group)

        response = {
            'settings': self.get_dict(settings, ad_group)
        }

        return self.create_api_response(response)

    def put(self, request, ad_group_id):
        try:
            ad_group = models.AdGroup.user_objects.get_for_user(request.user).\
                filter(id=int(ad_group_id)).get()
        except models.AdGroup.DoesNotExist:
            raise exc.MissingDataError('Ad Group does not exist')

        current_settings = self.get_current_settings(ad_group)

        resource = json.loads(request.body)

        form = forms.AdGroupSettingsForm(
            current_settings, resource.get('settings', {})
        )
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        self.set_ad_group(ad_group, form.cleaned_data)

        settings = models.AdGroupSettings()
        self.set_settings(settings, ad_group, form.cleaned_data)

        ad_group.save()
        settings.save()

        response = {
            'settings': self.get_dict(settings, ad_group)
        }

        return self.create_api_response(response)

    def get_current_settings(self, ad_group):
        settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('-created_dt')
        if settings:
            settings = settings[0]
        else:
            settings = models.AdGroupSettings(
                state=constants.AdGroupSettingsState.INACTIVE,
                start_date=datetime.datetime.utcnow().date(),
                cpc_cc=0.4000,
                daily_budget_cc=10.0000,
                target_devices=constants.AdTargetDevice.get_all()
            )

        return settings

    def get_dict(self, settings, ad_group):
        result = {}

        if settings:
            result = {
                'id': str(ad_group.pk),
                'name': ad_group.name,
                'state': settings.state,
                'start_date': settings.start_date,
                'end_date': settings.end_date,
                'cpc_cc': '{:.2f}'.format(settings.cpc_cc),
                'daily_budget_cc': '{:.2f}'.format(settings.daily_budget_cc),
                'target_devices': settings.target_devices,
                'target_regions': settings.target_regions,
                'tracking_code': settings.tracking_code
            }

        return result

    def set_ad_group(self, ad_group, resource):
        ad_group.name = resource['name']

    def set_settings(self, settings, ad_group, resource):
        # settings.ad_group = ad_group
        settings.ad_group = ad_group
        settings.state = resource['state']
        settings.start_date = resource['start_date']
        settings.end_date = resource['end_date']
        settings.cpc_cc = resource['cpc_cc']
        settings.daily_budget_cc = resource['daily_budget_cc']
        settings.target_devices = resource['target_devices']
        settings.target_regions = resource['target_regions']
        settings.tracking_code = resource['tracking_code']
