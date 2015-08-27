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

from django.db import transaction
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.views.decorators.http import require_GET

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

from dash import models
from dash import constants
from dash import regions
from dash import api
from dash import forms
from dash import upload

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
    return render(request, 'index.html', {'staticUrl': settings.CLIENT_STATIC_URL})


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

        self.add_settings_data(data, include_archived_flag)

        result = []
        for account in data.values():
            account['campaigns'] = account['campaigns'].values()
            result.append(account)

        return self.create_api_response(result)

    def add_settings_data(self, data, include_archived_flag):
        account_settingss = models.AccountSettings.objects.\
            order_by('account_id', '-created_dt').\
            distinct('account').\
            select_related('account')
        account_settingss = {acc_settings.account.id: acc_settings for acc_settings in account_settingss}

        campaign_settingss = models.CampaignSettings.objects.\
            order_by('campaign_id', '-created_dt').\
            distinct('campaign').\
            select_related('campaign')
        campaign_settingss = {camp_settings.campaign.id: camp_settings for camp_settings in campaign_settingss}

        ad_group_settingss = models.AdGroupSettings.objects.\
            order_by('ad_group_id', '-created_dt').\
            distinct('ad_group').\
            select_related('ad_group')
        ad_group_settingss = {ag_settings.ad_group.id: ag_settings for ag_settings in ad_group_settingss}

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
                    ad_group['status'] = constants.AdGroupRunningStatus.get_text(ad_group_settings.get_running_status() if ad_group_settings else constants.AdGroupSettingsState.INACTIVE).lower()
                    

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

        return self.create_api_response({})


class AccountRestore(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_restore_post')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        account.restore(request)

        return self.create_api_response({})


class CampaignArchive(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_archive_post')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.archive(request)

        return self.create_api_response({})


class CampaignRestore(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_restore_post')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.restore(request)

        return self.create_api_response({})


class AdGroupArchive(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_archive_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.archive(request)

        return self.create_api_response({})


class AdGroupRestore(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_restore_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.restore(request)

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
        ad_group.save(request)

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
                filter(source__in=filtered_sources).exclude(credentials__isnull=True):

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
            'sources': sources,
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
            raise exc.ValidationError('{} media source can not be added because it does not support DMA targeting.'\
                                      .format(source.name))

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=ad_group,
            source_credentials=default_settings.credentials,
            can_manage_content_ads=source.can_manage_content_ads(),
        )

        if source.source_type.type == constants.SourceType.GRAVITY:
            ad_group_source.source_campaign_key = settings.SOURCE_CAMPAIGN_KEY_PENDING_VALUE

        ad_group_source.save(request)

        external_name = ad_group_source.get_external_name()
        actionlog.api.create_campaign(ad_group_source, external_name, request)
        self._add_to_history(ad_group_source, request)

        return self.create_api_response(None)

    def _add_to_history(self, ad_group_source, request):
        changes_text = '{} campaign created.'.format(ad_group_source.source.name)

        settings = ad_group_source.ad_group.get_current_settings().copy_settings()
        settings.changes_text = changes_text
        settings.save(request)
        

    def _can_target_existing_regions(self, source, ad_group_settings):
        return (source.source_type.supports_dma_targeting() and ad_group_settings.targets_dma()) or\
            not ad_group_settings.targets_dma()


class Account(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_put')
    def put(self, request):
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        account = models.Account(name=create_name(models.Account.objects, 'New account'))
        account.save(request)

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

        return self.create_api_response()


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
                'call_to_action': current_settings.call_to_action
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
        display_url = form.cleaned_data['display_url']
        brand_name = form.cleaned_data['brand_name']
        description = form.cleaned_data['description']
        call_to_action = form.cleaned_data['call_to_action']
        content_ads = form.cleaned_data['content_ads']

        batch = models.UploadBatch.objects.create(
            name=batch_name,
            display_url=display_url,
            brand_name=brand_name,
            description=description,
            call_to_action=call_to_action,
            processed_content_ads=0,
            batch_size=len(content_ads)
        )

        current_settings = ad_group.get_current_settings()
        new_settings = current_settings.copy_settings()

        new_settings.display_url = display_url
        new_settings.brand_name = brand_name
        new_settings.description = description
        new_settings.call_to_action = call_to_action

        new_settings.save(request)

        upload.process_async(
            content_ads,
            request.FILES['content_ads'].name,
            batch,
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

        response_data = {'status': batch.status, 'count': batch.processed_content_ads, 'all': batch.batch_size}

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
        email_helper.send_ad_group_settings_change_mail_if_necessary(ad_group, request.user, request)

        return self.create_api_response()


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
                content_ad_dicts = [{ 'url': '', 'title': '', 'image_url': '' }]
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
            content_ad_dicts.append({
                'url': content_ad.url,
                'title': content_ad.title,
                'image_url': content_ad.get_original_image_url(),
            })

        filename = '{}_{}_{}_content_ads'.format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.name),
            datetime.datetime.now().strftime('%Y-%m-%d')
        )
        content = self._create_content_ad_csv(content_ad_dicts)

        return self.create_csv_response(filename, content=content)

    def _create_content_ad_csv(self, content_ads):
        string = StringIO.StringIO()

        writer = unicodecsv.DictWriter(string, ['url', 'title', 'image_url'])
        writer.writeheader()

        for row in content_ads:
            writer.writerow(row)

        return string.getvalue()


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
