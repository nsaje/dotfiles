import json

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from dash import api_common
from dash import exc
from dash import forms
from dash import models

import constants


# Create your views here.
@login_required(login_url=settings.LOGIN_URL)
def index(request):
    return render(request, 'index.html', {'staticUrl': settings.CLIENT_STATIC_URL})


class AdGroupSettings(api_common.BaseApiView):
    def get(self, request, ad_group_id):
        try:
            ad_group = models.AdGroup.user_objects.get_for_user(request.user).\
                filter(id=int(ad_group_id)).get()
        except models.AdGroup.DoesNotExist:
            raise exc.MissingDataError('Ad Group does not exist')

        settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('-created_dt')
        if settings:
            settings = settings[0]
        else:
            settings = models.AdGroupSettings(
                state=constants.AdGroupSettingsState.INACTIVE,

            )

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

        resource = json.loads(request.body)

        form = forms.AdGroupSettingsForm(resource.get('settings', {}))
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

    def get_dict(self, settings, ad_group):
        result = {}

        cpc_cc = settings.cpc_cc
        if cpc_cc is not None:
            cpc_cc = str(cpc_cc)

        daily_budget_cc = settings.daily_budget_cc
        if daily_budget_cc is not None:
            daily_budget_cc = str(daily_budget_cc)

        if settings:
            result = {
                'id': str(ad_group.pk),
                'name': ad_group.name,
                'state': settings.state,
                'start_date': settings.start_date,
                'end_date': settings.end_date,
                'cpc_cc': settings.cpc_cc,
                'daily_budget_cc': settings.daily_budget_cc,
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

    # def set_ad_group(self, ad_group, resource):
    #     if 'name' in resource:
    #         ad_group.name = resource['name']

    # def set_settings(self, settings, ad_group_id, resource):
    #     # settings.ad_group = ad_group
    #     settings.ad_group_id = ad_group_id

    #     if 'state' in resource:
    #         settings.state = resource['state']

    #     if 'start_date' in resource:
    #         settings.state = resource['start_date']

    #     if 'end_date' in resource:
    #         settings.state = resource['end_date']

    #     if 'cpc_cc' in resource:
    #         settings.state = resource['cpc_cc']

    #     if 'daily_budget_cc' in resource:
    #         settings.state = resource['daily_budget_cc']

    #     if 'target_devices' in resource:
    #         settings.state = resource['target_devices']

    #     if 'target_regions' in resource:
    #         settings.state = resource['target_regions']

    #     if 'tracking_code' in resource:
    #         settings.state = resource['tracking_code']
