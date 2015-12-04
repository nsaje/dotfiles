# -*- coding: utf-8 -*-
import datetime
import json
import decimal
import logging
import base64
import httplib
import urllib
import urllib2
import pytz
import os
import StringIO
import unicodecsv
import slugify
import hmac
import hashlib

from collections import OrderedDict

from django.db import transaction
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

from dash.views import helpers

from utils import statsd_helper
from utils import api_common
from utils import exc
from utils import s3helpers
from utils import email_helper

import actionlog.api
import actionlog.api_contentads
import actionlog.sync
import actionlog.zwei_actions
import actionlog.models
import actionlog.constants

from dash import models, region_targeting_helper
from dash import constants
from dash import api
from dash import forms
from dash import upload

import reports.api_publishers

logger = logging.getLogger(__name__)


def create_name(objects, name):
    objects = objects.filter(name__regex=r'^{}( [0-9]+)?$'.format(name))

    if len(objects):
        num = len(objects) + 1

        nums = [int(a.name.replace(name, '').strip() or 1) for a in objects]
        nums.sort()

        for i, j in enumerate(nums):
            # value can be used if index is smaller than value
            if (i + 1) < j:
                num = i + 1
                break

        if num > 1:
            name += ' {}'.format(num)

    return name


@statsd_helper.statsd_timer('dash', 'index')
@login_required
def index(request):
    return render(request, 'index.html', {'staticUrl': settings.CLIENT_STATIC_URL, 'debug': settings.DEBUG})


@statsd_helper.statsd_timer('dash', 'supply_dash_redirect')
@login_required
def supply_dash_redirect(request):
    # We do not authorization validation here since it only redirects to third-party
    # dashboards and if user can't access them, there is no harm done.
    ad_group_id = request.GET.get('ad_group_id')
    source_id = request.GET.get('source_id')

    validation_errors = {}
    if not ad_group_id:
        validation_errors['ad_group_id'] = 'Missing param ad_group_id.'

    if not source_id:
        validation_errors['source_id'] = 'Missing param source_id.'

    if validation_errors:
        raise exc.ValidationError(errors=validation_errors)

    try:
        ad_group_source = models.AdGroupSource.objects.get(
            ad_group__id=int(ad_group_id), source__id=int(source_id))
    except models.AdGroupSource.DoesNotExist:
        raise exc.MissingDataError()

    credentials = ad_group_source.source_credentials and \
        ad_group_source.source_credentials.decrypt()

    url_response = actionlog.zwei_actions.get_supply_dash_url(
        ad_group_source.source.source_type.type, credentials, ad_group_source.source_campaign_key)

    return render(request, 'redirect.html', {'url': url_response['url']})


class User(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'user_get')
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
                'name': user.get_full_name(),
                'show_onboarding_guidance': user.show_onboarding_guidance,
                'permissions': user.get_all_permissions_with_access_levels(),
                'timezone_offset': pytz.timezone(settings.DEFAULT_TIME_ZONE).utcoffset(
                    datetime.datetime.utcnow(), is_dst=True).total_seconds()
            }

        return result


@login_required
@require_GET
def demo_mode(request):
    demo_user = authenticate(username=settings.DEMO_USER_EMAIL, password=settings.DEMO_USER_PASSWORD)
    login(request, demo_user)
    return redirect('index')


class NavigationDataView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'navigation_data_view_get')
    def get(self, request):
        include_archived_flag = request.user.has_perm('zemauth.view_archived_entities')
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        data = {}
        self.fetch_ad_groups(data, request.user, filtered_sources)
        self.fetch_campaigns(data, request.user, filtered_sources)
        self.fetch_accounts(data, request.user, filtered_sources)

        self.add_settings_data(data, include_archived_flag, filtered_sources)

        result = []
        for account in data.values():
            account['campaigns'] = account['campaigns'].values()
            result.append(account)

        return self.create_api_response(result)

    def add_settings_data(self, data, include_archived_flag, filtered_sources):

        account_ids, campaign_ids, ad_group_ids = [], [], []

        # collect only relevant ids, so that we don't unnecessarly fetch
        # the entire set of account/campaign/ad group settings
        for account in data.values():
            account_ids.append(account['id'])
            for campaign in account['campaigns'].values():
                campaign_ids.append(campaign['id'])
                for ad_group in campaign['adGroups']:
                    ad_group_ids.append(ad_group['id'])

        account_settingss = models.AccountSettings.objects\
                                                  .filter(account_id__in=account_ids)\
                                                  .group_current_settings()
        account_settingss = {acc_settings.account_id: acc_settings for acc_settings in account_settingss}

        campaign_settingss = models.CampaignSettings.objects\
                                                    .filter(campaign_id__in=campaign_ids)\
                                                    .group_current_settings()
        campaign_settingss = {camp_settings.campaign_id: camp_settings for camp_settings in campaign_settingss}

        ad_group_settingss = models.AdGroupSettings.objects\
                                                   .filter(ad_group_id__in=ad_group_ids)\
                                                   .group_current_settings()
        ad_group_settingss = {ag_settings.ad_group_id: ag_settings for ag_settings in ad_group_settingss}

        ad_group_sources_settingss = models.AdGroupSourceSettings.objects\
                                                                 .filter(ad_group_source__ad_group_id__in=ad_group_ids)\
                                                                 .filter_by_sources(filtered_sources)\
                                                                 .group_current_settings()\
                                                                 .select_related('ad_group_source')
        sources_settings = {}
        for source_settings in ad_group_sources_settingss:
            key = source_settings.ad_group_source.ad_group_id
            sources_settings.setdefault(key, [])
            sources_settings[key].append(source_settings)

        for account in data.values():
            account_settings = account_settingss.get(account['id'])

            if include_archived_flag:
                account['archived'] = account_settings.archived if account_settings else False

            for campaign in account['campaigns'].values():
                campaign_settings = campaign_settingss.get(campaign['id'])

                if include_archived_flag:
                    campaign['archived'] = campaign_settings.archived if campaign_settings else False

                for ad_group in campaign['adGroups']:
                    ad_group_settings = ad_group_settingss.get(ad_group['id'])

                    if include_archived_flag:
                        ad_group['archived'] = ad_group_settings.archived if ad_group_settings else False

                    ad_group['state'] = constants.AdGroupSettingsState.get_text(
                        ad_group_settings.state if ad_group_settings
                        else constants.AdGroupSettingsState.INACTIVE
                    ).lower()

                    ad_group['status'] = constants.AdGroupRunningStatus.get_text(
                        models.AdGroupSettings.get_running_status(
                            ad_group_settings, sources_settings.get(ad_group['id'])
                        )
                    ).lower()

    def fetch_ad_groups(self, data, user, sources):
        ad_groups = models.AdGroup.objects.all().\
            filter_by_user(user).\
            filter_by_sources(sources).\
            select_related('campaign__account')

        for ad_group in ad_groups:
            campaign = ad_group.campaign
            account = campaign.account

            self.add_account_dict(data, account)

            campaigns = data[account.id]['campaigns']
            self.add_campaign_dict(campaigns, campaign)

            campaigns[campaign.id]['adGroups'].append(
                {
                    'id': ad_group.id,
                    'name': ad_group.name,
                    'contentAdsTabWithCMS': ad_group.content_ads_tab_with_cms,
                }
            )

    def fetch_campaigns(self, data, user, sources):
        campaigns = models.Campaign.objects.all().\
            filter_by_user(user).\
            filter_by_sources(sources).\
            select_related('account')

        for campaign in campaigns:
            account = campaign.account

            self.add_account_dict(data, account)
            self.add_campaign_dict(data[account.id]['campaigns'], campaign)

    def fetch_accounts(self, data, user, sources):
        accounts = models.Account.objects.all().\
            filter_by_user(user).\
            filter_by_sources(sources)

        for account in accounts:
            self.add_account_dict(data, account)

    def add_account_dict(self, data, account):
        if account.id not in data:
            data[account.id] = {
                'id': account.id,
                'name': account.name,
                'campaigns': {}
            }

    def add_campaign_dict(self, data, campaign):
        if campaign.id not in data:
            data[campaign.id] = {
                'id': campaign.id,
                'name': campaign.name,
                'adGroups': []
            }


class AccountArchive(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_archive_post')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        account.archive(request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.ARCHIVE_RESTORE_ACCOUNT, account=account)

        return self.create_api_response({})


class AccountRestore(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_restore_post')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        account.restore(request)

        actionlog.sync.AccountSync(account).trigger_all(self.request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.ARCHIVE_RESTORE_ACCOUNT, account=account)

        return self.create_api_response({})


class CampaignArchive(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_archive_post')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.archive(request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.ARCHIVE_RESTORE_CAMPAIGN,
                                            campaign=campaign)

        return self.create_api_response({})


class CampaignRestore(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_restore_post')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.restore(request)

        actionlog.sync.CampaignSync(campaign).trigger_all(self.request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.ARCHIVE_RESTORE_CAMPAIGN,
                                            campaign=campaign)

        return self.create_api_response({})


class AdGroupArchive(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_archive_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.archive(request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.ARCHIVE_RESTORE_AD_GROUP,
                                            ad_group=ad_group)

        return self.create_api_response({})


class AdGroupRestore(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_restore_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.restore(request)

        actionlog.sync.AdGroupSync(ad_group).trigger_all(self.request)

        for ad_group_source in ad_group.adgroupsource_set.all():
            api.refresh_publisher_blacklist(ad_group_source, request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.ARCHIVE_RESTORE_AD_GROUP,
                                            ad_group=ad_group)

        return self.create_api_response({})


class CampaignAdGroups(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaigns_ad_group_put')
    def put(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_ad_groups_view'):
            raise exc.MissingDataError()

        campaign = helpers.get_campaign(request.user, campaign_id)

        ad_group = models.AdGroup(
            name=create_name(models.AdGroup.objects.filter(campaign=campaign), 'New ad group'),
            campaign=campaign
        )

        actionlogs_to_send = []
        with transaction.atomic():
            ad_group.save(request)

            # always create settings when creating an ad group
            # and propagate them to external sources
            ad_group_settings = ad_group.get_current_settings()
            ad_group_settings.save(request)

            actionlogs_to_send.extend(
                api.order_ad_group_settings_update(
                    ad_group, models.AdGroupSettings(), ad_group_settings, request,
                    send=False
                )
            )

        helpers.log_useraction_if_necessary(request, constants.UserActionType.CREATE_AD_GROUP,
                                            ad_group=ad_group, campaign=campaign)

        actionlog.zwei_actions.send(actionlogs_to_send)

        response = {
            'name': ad_group.name,
            'id': ad_group.id,
            'content_ads_tab_with_cms': ad_group.content_ads_tab_with_cms
        }

        return self.create_api_response(response)


class AdGroupState(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_state_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('-created_dt')

        response = {
            'state': settings[0].state if settings
            else constants.AdGroupSettingsState.INACTIVE
        }

        return self.create_api_response(response)


class AvailableSources(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'available_sources_get')
    def get(self, request):
        show_archived = request.GET.get('show_archived') == 'true' and\
            request.user.has_perm('zemauth.view_archived_entities')
        user_ad_groups = models.AdGroup.objects.all().filter_by_user(request.user)
        if not show_archived:
            user_ad_groups = user_ad_groups.exclude_archived()

        demo_to_real_ad_groups = []
        for d2r in models.DemoAdGroupRealAdGroup.objects.filter(demo_ad_group__in=user_ad_groups):
            demo_to_real_ad_groups.append(d2r.real_ad_group)

        ad_groups = list(user_ad_groups) + demo_to_real_ad_groups

        sources = []
        for source in models.Source.objects.filter(adgroupsource__ad_group__in=[ag.id for ag in ad_groups]).distinct():
            sources.append({
                'id': str(source.id),
                'name': source.name,
                'deprecated': source.deprecated,
            })

        return self.create_api_response({
            'sources': sources
        })


class AdGroupSources(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_sources_add_source'):
            raise exc.MissingDataError()

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group_settings = ad_group.get_current_settings()

        if ad_group.is_demo:
            real_ad_groups = models.DemoAdGroupRealAdGroup.objects.filter(demo_ad_group=ad_group)
            if real_ad_groups:
                ad_group = real_ad_groups[0].real_ad_group

        ad_group_sources = ad_group.sources.all().order_by('name')

        sources = []
        for source_settings in models.DefaultSourceSettings.objects.\
                filter(source__in=filtered_sources).with_credentials():

            if source_settings.source in ad_group_sources:
                continue

            sources.append({
                'id': source_settings.source.id,
                'name': source_settings.source.name,
                'can_target_existing_regions': self._can_target_existing_regions(source_settings.source,
                                                                                 ad_group_settings)
            })

        sources_waiting = set([ad_group_source.source.name for ad_group_source
                               in actionlog.api.get_ad_group_sources_waiting(ad_group=ad_group)])

        return self.create_api_response({
            'sources': sorted(sources, key=lambda source: source['name']),
            'sources_waiting': list(sources_waiting),
        })

    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_put')
    def put(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_sources_add_source'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        source_id = json.loads(request.body)['source_id']
        source = models.Source.objects.get(id=source_id)

        try:
            default_settings = models.DefaultSourceSettings.objects.get(source=source)
        except models.DefaultSourceSettings.DoesNotExist:
            raise exc.MissingDataError('No default settings set for {}.'.format(source.name))

        if not default_settings.credentials:
            raise exc.MissingDataError('No default credentials set in {}.'.format(default_settings))

        if models.AdGroupSource.objects.filter(source=source, ad_group=ad_group).exists():
            raise exc.ForbiddenError('{} media source for ad group {} already exists.'.format(source.name, ad_group_id))

        if not self._can_target_existing_regions(source, ad_group.get_current_settings()):
            raise exc.ValidationError('{} media source can not be added because it does not support selected region targeting.'\
                                      .format(source.name))

        ad_group_source = helpers.add_source_to_ad_group(default_settings, ad_group)
        ad_group_source.save(request)

        external_name = ad_group_source.get_external_name()
        actionlog.api.create_campaign(ad_group_source, external_name, request)
        self._add_to_history(ad_group_source, request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.CREATE_MEDIA_SOURCE_CAMPAIGN,
                                            ad_group=ad_group)

        if request.user.has_perm('zemauth.add_media_sources_automatically'):
            helpers.set_ad_group_source_defaults(default_settings, ad_group.get_current_settings(), ad_group_source,
                                                 request)

        return self.create_api_response(None)

    def _add_to_history(self, ad_group_source, request):
        changes_text = '{} campaign created.'.format(ad_group_source.source.name)

        settings = ad_group_source.ad_group.get_current_settings().copy_settings()
        settings.changes_text = changes_text
        settings.save(request)

    def _can_target_existing_regions(self, source, ad_group_settings):
        return region_targeting_helper.can_modify_selected_target_regions_automatically(source, ad_group_settings) or\
               region_targeting_helper.can_modify_selected_target_regions_manually(source, ad_group_settings)


class Account(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_put')
    def put(self, request):
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        account = models.Account(name=create_name(models.Account.objects, 'New account'))
        account.save(request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.CREATE_ACCOUNT, account=account)

        response = {
            'name': account.name,
            'id': account.id
        }

        return self.create_api_response(response)


class AccountCampaigns(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_campaigns_put')
    def put(self, request, account_id):
        if not request.user.has_perm('zemauth.account_campaigns_view'):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)
        account_settings = account.get_current_settings()

        name = create_name(models.Campaign.objects.filter(account=account), 'New campaign')

        campaign = models.Campaign(
            name=name,
            account=account
        )
        campaign.save(request)

        settings = models.CampaignSettings(
            name=name,
            campaign=campaign,
            account_manager=(account_settings.default_account_manager
                             if account_settings.default_account_manager else request.user),
            sales_representative=(account_settings.default_sales_representative
                                  if account_settings.default_sales_representative else None)
        )
        settings.save(request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.CREATE_CAMPAIGN,
                                            campaign=campaign)

        response = {
            'name': campaign.name,
            'id': campaign.id
        }

        return self.create_api_response(response)


class AdGroupSourceSettings(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_source_settings_put')
    def put(self, request, ad_group_id, source_id):
        if not request.user.has_perm('zemauth.set_ad_group_source_settings'):
            raise exc.ForbiddenError(message='Not allowed')

        resource = json.loads(request.body)

        try:
            ad_group = models.AdGroup.objects.all().filter_by_user(request.user).get(id=ad_group_id)
        except models.AdGroup.DoesNotExist:
            raise exc.MissingDataError(message='Requested ad group not found')

        try:
            ad_group_source = models.AdGroupSource.objects.get(ad_group=ad_group, source_id=source_id)
        except models.AdGroupSource.DoesNotExist:
            raise exc.MissingDataError(message='Requested source not found')

        settings_writer = api.AdGroupSourceSettingsWriter(ad_group_source)

        errors = {}

        state_form = forms.AdGroupSourceSettingsStateForm(resource)
        if 'state' in resource and not state_form.is_valid():
            errors.update(state_form.errors)

        cpc_form = forms.AdGroupSourceSettingsCpcForm(resource, ad_group_source=ad_group_source)
        if 'cpc_cc' in resource and not cpc_form.is_valid():
            errors.update(cpc_form.errors)

        daily_budget_form = forms.AdGroupSourceSettingsDailyBudgetForm(resource, ad_group_source=ad_group_source)
        if 'daily_budget_cc' in resource and not daily_budget_form.is_valid():
            errors.update(daily_budget_form.errors)

        autopilot_form = forms.AdGroupSourceSettingsAutopilotStateForm(resource)
        if 'autopilot_state' in resource and not autopilot_form.is_valid():
            errors.update(autopilot_form.errors)

        if not request.user.has_perm('zemauth.can_set_media_source_to_auto_pilot') and\
                'autopilot_state' in resource and\
                resource['autopilot_state'] == constants.AdGroupSourceSettingsAutopilotState.ACTIVE:
            errors.update(exc.ForbiddenError(message='Not allowed'))

        if errors:
            raise exc.ValidationError(errors=errors)

        if 'cpc_cc' in resource:
            resource['cpc_cc'] = decimal.Decimal(resource['cpc_cc'])
        if 'daily_budget_cc' in resource:
            resource['daily_budget_cc'] = decimal.Decimal(resource['daily_budget_cc'])

        if 'cpc_cc' in resource or 'daily_budget_cc' in resource:
            end_datetime = ad_group.get_current_settings().get_utc_end_datetime()
            if end_datetime is not None and end_datetime <= datetime.datetime.utcnow():
                raise exc.ValidationError()

        settings_writer.set(resource, request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.SET_MEDIA_SOURCE_SETTINGS,
                                            ad_group=ad_group)

        return self.create_api_response({
            'editable_fields': helpers.get_editable_fields(
                ad_group_source,
                ad_group_source.ad_group.get_current_settings(),
                ad_group_source.get_current_settings_or_none(),
                request.user
            )
        })


class AdGroupAdsPlusUpload(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.upload_content_ads'):
            raise exc.ForbiddenError(message='Not allowed')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        current_settings = ad_group.get_current_settings()

        return self.create_api_response({
            'defaults': {
                'display_url': current_settings.display_url,
                'brand_name': current_settings.brand_name,
                'description': current_settings.description,
                'call_to_action': current_settings.call_to_action or 'Read More'
            }
        })

    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.upload_content_ads'):
            raise exc.ForbiddenError(message='Not allowed')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        form = forms.AdGroupAdsPlusUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            raise exc.ValidationError(errors=form.errors)

        batch_name = form.cleaned_data['batch_name']
        content_ads = form.cleaned_data['content_ads']

        # we could have passed form.cleaned_data around,
        # but it's better to have a version that is more predictable
        upload_form_cleaned_fields = {
            'display_url': form.cleaned_data['display_url'],
            'brand_name': form.cleaned_data['brand_name'],
            'description': form.cleaned_data['description'],
            'call_to_action': form.cleaned_data['call_to_action']
        }

        batch = models.UploadBatch.objects.create(
            name=batch_name,
            processed_content_ads=0,
            batch_size=len(content_ads),
        )

        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()

        new_settings.display_url = upload_form_cleaned_fields['display_url']
        new_settings.brand_name = upload_form_cleaned_fields['brand_name']
        new_settings.description = upload_form_cleaned_fields['description']
        new_settings.call_to_action = upload_form_cleaned_fields['call_to_action']

        new_settings.save(request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.UPLOAD_CONTENT_ADS,
                                            ad_group=ad_group)

        upload.process_async(
            content_ads,
            request.FILES['content_ads'].name,
            batch,
            upload_form_cleaned_fields,
            ad_group,
            request
        )

        return self.create_api_response({'batch_id': batch.pk})


class AdGroupAdsPlusUploadReport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_report_get')
    def get(self, request, ad_group_id, batch_id):
        if not request.user.has_perm('zemauth.upload_content_ads'):
            raise exc.ForbiddenError(message='Not allowed')

        helpers.get_ad_group(request.user, ad_group_id)

        try:
            batch = models.UploadBatch.objects.get(pk=batch_id)
        except models.UploadBatch.DoesNotExist():
            raise exc.MissingDataException()

        content = s3helpers.S3Helper().get(batch.error_report_key)
        basefnm, _ = os.path.splitext(
            os.path.basename(batch.error_report_key))

        name = basefnm.rsplit('_', 1)[0] + '_errors'

        return self.create_csv_response(name, content=content)


class AdGroupAdsPlusUploadStatus(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_status_get')
    def get(self, request, ad_group_id, batch_id):
        if not request.user.has_perm('zemauth.upload_content_ads'):
            raise exc.ForbiddenError(message='Not allowed')

        helpers.get_ad_group(request.user, ad_group_id)

        try:
            batch = models.UploadBatch.objects.get(pk=batch_id)
        except models.UploadBatch.DoesNotExist():
            raise exc.MissingDataException()

        batch_size = batch.batch_size
        step_size = batch_size

        if batch.inserted_content_ads is not None and batch.inserted_content_ads >= batch_size:
            # step past inserting
            step = 'Sending to external sources (step 3/3)'
            count = 0
            step_size = 0
        elif batch.inserted_content_ads is not None:
            step = 'Inserting content ads (step 2/3)'
            count = batch.inserted_content_ads
        else:
            step = 'Processing imported file (step 1/3)'
            count = batch.processed_content_ads

        response_data = {
            'status': batch.status,
            'step': step,
            'count': count or 0,
            'all': step_size
        }

        if batch.status == constants.UploadBatchStatus.FAILED:
            if batch.error_report_key:
                text = '{} error{}. <a href="{}">Download Report.</a>'.format(
                    batch.num_errors,
                    's' if batch.num_errors > 1 else '',
                    reverse(
                        'ad_group_ads_plus_upload_report',
                        kwargs={'ad_group_id': ad_group_id, 'batch_id': batch.id})
                )
            else:
                text = 'An error occured while processing file.'

            response_data['errors'] = {'content_ads': [text]}

        return self.create_api_response(response_data)


class AdGroupContentAdArchive(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_content_ad_archive_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.ForbiddenError(message="Not allowed")

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        data = json.loads(request.body)

        select_all = data.get('select_all', False)
        select_batch_id = data.get('select_batch')

        content_ad_ids_selected = helpers.parse_post_request_content_ad_ids(data, 'content_ad_ids_selected')
        content_ad_ids_not_selected = helpers.parse_post_request_content_ad_ids(data, 'content_ad_ids_not_selected')

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=False
        )

        active_content_ads = [ad for ad in content_ads if ad.state == constants.ContentAdSourceState.ACTIVE]
        if active_content_ads:
            api.update_content_ads_state(active_content_ads, constants.ContentAdSourceState.INACTIVE, request)

        response = {
            'active_count': len(active_content_ads)
        }

        # reload
        content_ads = content_ads.all()

        api.add_content_ads_archived_change_to_history(ad_group, content_ads, True, request)
        email_helper.send_ad_group_notification_email(ad_group, request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.ARCHIVE_RESTORE_CONTENT_AD,
                                            ad_group=ad_group)

        with transaction.atomic():
            for content_ad in content_ads:
                content_ad.archived = True
                content_ad.save()

        response['archived_count'] = len(content_ads)
        response['rows'] = {
            content_ad.id: {
                'archived': content_ad.archived,
                'status_setting': content_ad.state,
            }
            for content_ad in content_ads
        }

        return self.create_api_response(response)


class AdGroupContentAdRestore(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_content_ad_restore_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.ForbiddenError(message="Not allowed")

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        data = json.loads(request.body)

        select_all = data.get('select_all', False)
        select_batch_id = data.get('select_batch')

        content_ad_ids_selected = helpers.parse_post_request_content_ad_ids(data, 'content_ad_ids_selected')
        content_ad_ids_not_selected = helpers.parse_post_request_content_ad_ids(data, 'content_ad_ids_not_selected')

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=True
        )

        api.add_content_ads_archived_change_to_history(ad_group, content_ads, False, request)
        email_helper.send_ad_group_notification_email(ad_group, request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.ARCHIVE_RESTORE_CONTENT_AD,
                                            ad_group=ad_group)

        with transaction.atomic():
            for content_ad in content_ads:
                content_ad.archived = False
                content_ad.save()

        return self.create_api_response({
            'rows': {content_ad.id: {
                'archived': content_ad.archived,
                'status_setting': content_ad.state,
            } for content_ad in content_ads}})


class AdGroupContentAdState(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_content_ad_state_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.set_content_ad_status'):
            raise exc.ForbiddenError(message='Not allowed')

        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        data = json.loads(request.body)

        state = data.get('state')
        if state is None or state not in constants.ContentAdSourceState.get_all():
            raise exc.ValidationError()
        select_all = data.get('select_all', False)
        select_batch_id = data.get('select_batch')

        content_ad_ids_selected = helpers.parse_post_request_content_ad_ids(data, 'content_ad_ids_selected')
        content_ad_ids_not_selected = helpers.parse_post_request_content_ad_ids(data, 'content_ad_ids_not_selected')

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived=False
        )

        api.update_content_ads_state(content_ads, state, request)
        api.add_content_ads_state_change_to_history(ad_group, content_ads, state, request)
        email_helper.send_ad_group_notification_email(ad_group, request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.SET_CONTENT_AD_STATE,
                                            ad_group=ad_group)

        return self.create_api_response()


CSV_EXPORT_COLUMN_NAMES_DICT = OrderedDict([
    ['url', 'url'],
    ['title', 'title'],
    ['image_url', 'image_url'],
    ['description', 'description (optional)'],
    ['crop_areas', 'crop areas (optional)'],
    ['tracker_urls', 'tracker url (optional)']
])


class AdGroupContentAdCSV(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_content_ad_state_post')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.get_content_ad_csv'):
            raise exc.ForbiddenError(message='Not allowed')

        try:
            ad_group = helpers.get_ad_group(request.user, ad_group_id)
        except exc.MissingDataError, e:
            email = request.user.email
            if email == settings.DEMO_USER_EMAIL or email in settings.DEMO_USERS:
                content_ad_dicts = [{'url': '', 'title': '', 'image_url': '', 'description': ''}]
                content = self._create_content_ad_csv(content_ad_dicts)
                return self.create_csv_response('contentads', content=content)
            raise e

        select_all = request.GET.get('select_all', False)
        select_batch_id = request.GET.get('select_batch')
        include_archived = request.GET.get('archived') == 'true' and\
            request.user.has_perm('zemauth.view_archived_entities')

        content_ad_ids_selected = helpers.parse_get_request_content_ad_ids(request.GET, 'content_ad_ids_selected')
        content_ad_ids_not_selected = helpers.parse_get_request_content_ad_ids(request.GET, 'content_ad_ids_not_selected')

        content_ads = helpers.get_selected_content_ads(
            ad_group_id,
            select_all,
            select_batch_id,
            content_ad_ids_selected,
            content_ad_ids_not_selected,
            include_archived
        )

        content_ad_dicts = []
        for content_ad in content_ads:
            content_ad_dict = {
                'url': content_ad.url,
                'title': content_ad.title,
                'image_url': content_ad.get_original_image_url(),
                'display_url': content_ad.display_url,
                'brand_name': content_ad.brand_name,
                'description': content_ad.description,
                'call_to_action': content_ad.call_to_action,
            }

            if content_ad.crop_areas:
                content_ad_dict['crop_areas'] = content_ad.crop_areas

            if content_ad.tracker_urls:
                content_ad_dict['tracker_urls'] = ' '.join(content_ad.tracker_urls)

            # delete keys that are not to be exported
            for k in content_ad_dict.keys():
                if k not in CSV_EXPORT_COLUMN_NAMES_DICT.keys():
                    del content_ad_dict[k]

            content_ad_dicts.append(content_ad_dict)

        filename = '{}_{}_{}_content_ads'.format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.name),
            datetime.datetime.now().strftime('%Y-%m-%d')
        )
        content = self._create_content_ad_csv(content_ad_dicts)

        return self.create_csv_response(filename, content=content)

    def _create_content_ad_csv(self, content_ads):
        string = StringIO.StringIO()

        writer = unicodecsv.DictWriter(string, CSV_EXPORT_COLUMN_NAMES_DICT.keys())

        # write the header manually as it is different than keys in the dict
        writer.writerow(CSV_EXPORT_COLUMN_NAMES_DICT)

        for row in content_ads:
            writer.writerow(row)

        return string.getvalue()


class PublishersBlacklistStatus(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'ad_group_publisher_blacklist_state_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.can_modify_publisher_blacklist_status'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        body = json.loads(request.body)

        start_date = helpers.parse_datetime(body.get('start_date'))
        end_date = helpers.parse_datetime(body.get('end_date'))

        state = int(body.get('state'))
        if state not in constants.PublisherStatus.get_all():
            raise exc.MissingDataError('Invalid state')

        level = body.get('level')
        if level not in constants.PublisherBlacklistLevel.get_all():
            raise exc.MissingDataError('Invalid level')

        if level in (constants.PublisherBlacklistLevel.CAMPAIGN,
                     constants.PublisherBlacklistLevel.ACCOUNT) and\
                not request.user.has_perm('zemauth.can_access_campaign_account_publisher_blacklist_status'):
            raise exc.AuthorizationError()

        if level == constants.PublisherBlacklistLevel.GLOBAL and\
                not request.user.has_perm('zemauth.can_access_global_publisher_blacklist_status'):
            raise exc.AuthorizationError()

        publishers_selected = body["publishers_selected"]
        publishers_not_selected = body["publishers_not_selected"]

        select_all = body["select_all"]
        publishers = []
        if select_all:
            publishers = self._query_all_publishers(ad_group, start_date, end_date)

        # update with pending statuses
        if level in (constants.PublisherBlacklistLevel.ADGROUP,
                     constants.PublisherBlacklistLevel.CAMPAIGN,
                     constants.PublisherBlacklistLevel.ACCOUNT,):
            self._handle_adgroup_blacklist(request, ad_group, level, state, publishers, publishers_selected, publishers_not_selected)

        if level == constants.PublisherBlacklistLevel.GLOBAL:
            self._handle_global_blacklist(request, ad_group, state, publishers, publishers_selected, publishers_not_selected)

        response = {
            "success": True,
        }
        return self.create_api_response(response)

    def _query_all_publishers(self, ad_group, start_date, end_date):
        source_cache_by_slug = {
            'outbrain': models.Source.objects.get(tracking_slug=constants.SourceType.OUTBRAIN)
        }

        # get all publishers from date range with statistics
        # (they represent select-all)
        constraints = {
            'ad_group': ad_group.id,
        }
        breakdown = ['exchange', 'domain']
        publishers = reports.api_publishers.query_publisher_list(
            start_date,
            end_date,
            breakdown_fields=breakdown,
            constraints=constraints
        )
        for publisher in publishers:
            source_slug = publisher['exchange']
            if source_slug not in source_cache_by_slug:
                source_cache_by_slug[source_slug] =\
                    models.Source.objects.get(bidder_slug=source_slug)
            publisher['source_id'] = source_cache_by_slug[source_slug].id
        return publishers

    def _handle_adgroup_blacklist(self, request, ad_group, level, state, publishers, publishers_selected, publishers_not_selected):
        ignored_publishers = set( [(pub['domain'], ad_group.id, pub['source_id'], )
            for pub in publishers_not_selected]
        )

        publishers_to_add = self._create_adgroup_blacklist(
            ad_group,
            publishers + publishers_selected,
            state,
            level,
            ignored_publishers
        )

        publisher_blacklist = [
            {
                'domain': dom,
                'ad_group_id': adgroup_id,
                'source': source,
            }\
            for (dom, adgroup_id, source,) in publishers_to_add
        ]

        # when blacklisting at campaign or account level we also need
        # to generate blacklist entries on external sources
        # for all adgroups in campaign or account
        related_publisher_blacklist = self._create_campaign_and_account_blacklist(ad_group, level, publishers + publishers_selected)

        if len(publisher_blacklist) > 0:
            actionlogs_to_send = []
            with transaction.atomic():
                actionlogs_to_send.extend(
                    api.create_publisher_blacklist_actions(
                        ad_group,
                        state,
                        level,
                        publisher_blacklist + related_publisher_blacklist,
                        request,
                        send=False
                    )
                )
            actionlog.zwei_actions.send(actionlogs_to_send)
            self._add_to_history(request, ad_group, state, publisher_blacklist)

    def _create_campaign_and_account_blacklist(self, ad_group, level, publishers):
        if level not in (constants.PublisherBlacklistLevel.CAMPAIGN,
                         constants.PublisherBlacklistLevel.ACCOUNT):
            return []

        ad_groups_on_level = []
        if level == constants.PublisherBlacklistLevel.CAMPAIGN:
            ad_groups_on_level = models.AdGroup.objects.filter(
                campaign=ad_group.campaign
            ).exclude(
                id=ad_group.id
            )
        elif level == constants.PublisherBlacklistLevel.ACCOUNT:
            ad_groups_on_level = models.AdGroup.objects.filter(
                campaign__account=ad_group.campaign.account
            ).exclude(
                id=ad_group.id
            )

        # filter archived
        filtered_ad_groups = [adg for adg in ad_groups_on_level if not adg.is_archived()]

        ret = []
        source_cache = {}
        for publisher in publishers:
            domain = publisher['domain']
            if domain not in source_cache:
               source_cache[domain] = models.Source.objects.filter(id=publisher['source_id']).first()
            source = source_cache[domain]

            # get all adgroups
            for ad_group in filtered_ad_groups:
                ret.append({
                    'domain': domain,
                    'ad_group_id': ad_group.id,
                    'source': source,
                })

        return ret

    def _create_adgroup_blacklist(self, ad_group, publishers, state, level, ignored_publishers):
        adgroup_blacklist = set([])
        failed_publisher_mappings = set([])
        count_failed_publisher = 0
        source_cache = {}

        for publisher in publishers:
            domain = publisher['domain']
            if domain not in source_cache:
               source_cache[domain]  = models.Source.objects.filter(id=publisher['source_id']).first()
            source = source_cache[domain]

            if not source:
                failed_publisher_mappings.add(publisher['domain'])
                count_failed_publisher += 1
                continue

            # we currently display sources for which we don't yet have publisher
            # blacklisting support
            if not source.can_modify_publisher_blacklist_automatically():
                continue

            if (domain, ad_group.id, source.id,) in ignored_publishers:
                continue

            blacklist_global = False
            if level == constants.PublisherBlacklistLevel.GLOBAL:
                blacklist_global = True
            blacklist_account = None
            if level == constants.PublisherBlacklistLevel.ACCOUNT:
                blacklist_account = ad_group.campaign.account
            blacklist_campaign = None
            if level == constants.PublisherBlacklistLevel.CAMPAIGN:
                blacklist_campaign = ad_group.campaign
            blacklist_ad_group = None
            if level == constants.PublisherBlacklistLevel.ADGROUP:
                blacklist_ad_group = ad_group

            # store blacklisted publishers and push to other sources
            existing_entry = models.PublisherBlacklist.objects.filter(
                name=publisher['domain'],
                source=source,
                everywhere=blacklist_global,
                account=blacklist_account,
                campaign=blacklist_campaign,
                ad_group=blacklist_ad_group
            ).first()

            # don't create pending pub. blacklist entry
            if existing_entry is not None and existing_entry.status == state:
                continue

            if existing_entry is None and state == constants.PublisherStatus.ENABLED:
                continue

            if existing_entry is not None:
                existing_entry.status = constants.PublisherStatus.PENDING
                existing_entry.save()
            else:
                models.PublisherBlacklist.objects.create(
                    name=publisher['domain'],
                    everywhere=blacklist_global,
                    account=blacklist_account,
                    campaign=blacklist_campaign,
                    ad_group=blacklist_ad_group,
                    source=source,
                    status=constants.PublisherStatus.PENDING
                )

            adgroup_blacklist.add(
                (domain, ad_group.id, source,)
            )
        if len(failed_publisher_mappings) > 0:
            logger.warning('Failed mapping {count} publisher source slugs {slug}'.format(
                count=count_failed_publisher,
                slug=','.join(failed_publisher_mappings))
            )
        return adgroup_blacklist

    def _handle_global_blacklist(self, request, ad_group, state, publishers, publishers_selected, publishers_not_selected):
        existing_blacklisted_publishers = models.PublisherBlacklist.objects.filter(
            everywhere=True
        ).values('name', 'source__id')

        existing_blacklisted_publishers = set(map(
            lambda pub: (pub['name'], pub['source__id'],),
            existing_blacklisted_publishers
        ))

        ignored_publishers = set([(pub['domain'], pub['source_id'])
            for pub in publishers_not_selected]
        )

        global_publishers = self._create_global_blacklist(
            ad_group,
            publishers + publishers_selected,
            state,
            existing_blacklisted_publishers.union(ignored_publishers),
            ignored_publishers,
        )
        global_blacklist = [
            {
                'domain': pub.name,
                'source': pub.source
            }\
            for pub in global_publishers
        ]

        if len(global_blacklist) > 0:
            actionlogs_to_send = []
            with transaction.atomic():
                actionlogs_to_send.extend(
                    api.create_global_publisher_blacklist_actions(
                        ad_group,
                        request,
                        state,
                        global_blacklist,
                        send=False
                    )
                )
            actionlog.zwei_actions.send(actionlogs_to_send)
            self._add_to_history(request, ad_group, state, global_blacklist)

    def _create_global_blacklist(self, ad_group, publishers, state, existing_blacklisted_publishers, ignored_publishers):
        blacklist = []
        source_cache = {}
        with transaction.atomic():
            for publisher in publishers:
                domain = publisher['domain']

                source_id = publisher.get('source_id')
                if source_id not in source_cache:
                    source_cache[source_id] = models.Source.objects.filter(id=source_id).first()
                source = source_cache.get(source_id)

                # we currently display sources for which we don't yet have publisher
                # blacklisting support
                if not source.can_modify_publisher_blacklist_automatically():
                    continue

                if source is None:
                    continue

                if (domain, source_id,) in ignored_publishers:
                    continue

                if state == constants.PublisherStatus.BLACKLISTED and\
                        (domain, source_id,) in existing_blacklisted_publishers:
                    continue

                # store blacklisted publishers and push to other sources
                new_entry = None
                existing_entry = models.PublisherBlacklist.objects.filter(
                    name=domain,
                    source=source,
                    everywhere=True
                ).first()
                if existing_entry is not None:
                    existing_entry.status = constants.PublisherStatus.PENDING
                    existing_entry.save()
                else:
                    new_entry = models.PublisherBlacklist.objects.create(
                        name=publisher['domain'],
                        source=source,
                        everywhere=True,
                        status=constants.PublisherStatus.PENDING
                    )
                blacklist.append(new_entry or existing_entry)
        return blacklist

    def _add_to_history(self, request, ad_group, state, blacklist):
        changes_text = '{action} the following publishers {pubs}.'.format(
            action="Blacklisted" if state == constants.PublisherStatus.BLACKLISTED else "Enabled",
            pubs=", ".join( ("{pub} on {slug}".format(pub=pub_bl['domain'], slug=pub_bl['source'].name)
                 for pub_bl in blacklist)
            )
        )
        settings = ad_group.get_current_settings().copy_settings()
        settings.changes_text = changes_text
        settings.save(request)
        email_helper.send_ad_group_notification_email(ad_group, request)


@statsd_helper.statsd_timer('dash', 'healthcheck')
def healthcheck(request):
    return HttpResponse('OK')


@login_required
def oauth_authorize(request, source_name):
    credentials_id = request.GET.get('credentials_id')

    if not credentials_id:
        logger.warning('Missing credentials id')
        return redirect('index')

    credentials = models.SourceCredentials.objects.get(id=credentials_id)
    decrypted = json.loads(credentials.decrypt())

    if 'client_id' not in decrypted or 'client_secret' not in decrypted:
        logger.error('client_id and/or client_secret not in credentials')
        return redirect('index')

    state = {
        'credentials_id': credentials_id,
    }

    redirect_uri = request.build_absolute_uri(reverse('source.oauth.redirect', kwargs={'source_name': source_name}))
    redirect_uri = redirect_uri.replace('http://', 'https://')

    params = {
        'client_id': decrypted['client_id'],
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'state': base64.b64encode(json.dumps(state))
    }

    url = settings.SOURCE_OAUTH_URIS[source_name]['auth_uri'] + '?' + urllib.urlencode(params)
    return redirect(url)


def oauth_redirect(request, source_name):
    # Token requests are implemented using urllib2 requests because Yahoo only supports credentials in
    # Authorization header while oauth2client sends it in reqeust body (for get_token calls, after that
    # it puts access token into header).

    code = request.GET.get('code')
    state = request.GET.get('state')

    if not state:
        logger.error('Missing state in OAuth2 redirect')
        return redirect('index')

    try:
        state = json.loads(base64.b64decode(state))
    except (TypeError, ValueError):
        logger.error('Invalid state in OAuth2 redirect')
        return redirect('index')

    credentials = models.SourceCredentials.objects.get(id=state['credentials_id'])
    decrypted = json.loads(credentials.decrypt())

    redirect_uri = request.build_absolute_uri(reverse('source.oauth.redirect', kwargs={'source_name': source_name}))
    redirect_uri = redirect_uri.replace('http://', 'https://')

    headers = {
        'Authorization': 'Basic {}'.format(base64.b64encode(decrypted['client_id'] + ':' + decrypted['client_secret']))
    }

    data = {
        'redirect_uri': redirect_uri,
        'code': code,
        'grant_type': 'authorization_code'
    }

    req = urllib2.Request(
        settings.SOURCE_OAUTH_URIS[source_name]['token_uri'],
        data=urllib.urlencode(data),
        headers=headers
    )
    r = urllib2.urlopen(req)

    if r.getcode() == httplib.OK:
        decrypted['oauth_tokens'] = json.loads(r.read())
        decrypted['oauth_created_dt'] = datetime.datetime.utcnow().isoformat()
        credentials.credentials = json.dumps(decrypted)
        credentials.save()

    return redirect(reverse('admin:dash_sourcecredentials_change', args=(credentials.id,)))


@statsd_helper.statsd_timer('dash', 'sharethrough_approval')
@csrf_exempt
def sharethrough_approval(request):
    data = json.loads(request.body)

    logger.info('sharethrough approval, content ad id: %s, status: %s', data['crid'], data['status'])

    sig = request.GET.get('sig')
    if not sig:
        logger.warning('Sharethrough approval postback without signature. crid: %s', data['crid'])
    else:
        calculated = base64.urlsafe_b64encode(hmac.new(settings.SHARETHROUGH_PARAM_SIGN_KEY,
                                                       msg=str(data['crid']),
                                                       digestmod=hashlib.sha256)).digest()

        if sig != calculated:
            logger.warning('Invalid sharethrough signature. crid: %s', data['crid'])

    content_ad_source = models.ContentAdSource.objects.get(content_ad_id=data['crid'],
                                                           source=models.Source.objects.get(name='Sharethrough'))

    if data['status'] == 0:
        content_ad_source.submission_status = constants.ContentAdSubmissionStatus.APPROVED
    else:
        content_ad_source.submission_status = constants.ContentAdSubmissionStatus.REJECTED

    content_ad_source.save()

    actionlog.api_contentads.init_update_content_ad_action(content_ad_source, {'state': content_ad_source.state},
                                                           request=None, send=True)

    return HttpResponse('OK')
