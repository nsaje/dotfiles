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

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import login, authenticate
from django.views.decorators.http import require_GET
from django.db import transaction

from dash.views import helpers

from utils import statsd_helper
from utils import api_common
from utils import exc
from utils.threads import BaseThread
from utils import request_provider

import actionlog.api
import actionlog.api_contentads
import actionlog.sync
import actionlog.zwei_actions

from dash import models
from dash import constants
from dash import api
from dash import forms
from dash import image

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
        ad_group_source.source_credentials.credentials

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
                'permissions': user.get_all_permissions_with_access_levels(),
                'timezone_offset': pytz.timezone(settings.DEFAULT_TIME_ZONE).utcoffset(
                    datetime.datetime.utcnow()).total_seconds()
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
            distinct('account')
        account_settingss = {acc_settings.account.id: acc_settings for acc_settings in account_settingss}

        campaign_settingss = models.CampaignSettings.objects.\
            order_by('campaign_id', '-created_dt').\
            distinct('campaign')
        campaign_settingss = {camp_settings.campaign.id: camp_settings for camp_settings in campaign_settingss}

        ad_group_settingss = models.AdGroupSettings.objects.\
            order_by('ad_group_id', '-created_dt').\
            distinct('ad_group')
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

            campaigns[campaign.id]['adGroups'].append({'id': ad_group.id, 'name': ad_group.name})

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
        account.archive()

        return self.create_api_response({})


class AccountRestore(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_restore_post')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        account.restore()

        return self.create_api_response({})


class CampaignArchive(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_archive_post')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.archive()

        return self.create_api_response({})


class CampaignRestore(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_restore_post')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.restore()

        return self.create_api_response({})


class AdGroupArchive(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_archive_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.archive()

        return self.create_api_response({})


class AdGroupRestore(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_restore_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.restore()

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
        ad_group.save()

        response = {
            'name': ad_group.name,
            'id': ad_group.id
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

        ad_group_sources = ad_group.sources.all().order_by('name')

        sources = []
        for source_settings in models.DefaultSourceSettings.objects.\
            filter(source__in=filtered_sources).\
            exclude(credentials__isnull=True):

            if source_settings.source in ad_group_sources:
                continue

            sources.append({
                'id': source_settings.source.id,
                'name': source_settings.source.name
            })

        sources_waiting = set([ad_group_source.source.name for ad_group_source
                               in actionlog.api.get_ad_group_sources_waiting(ad_group=ad_group)])

        return self.create_api_response({
            'sources': sources,
            'sources_waiting': list(sources_waiting)
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

        ad_group_source = models.AdGroupSource(
            source=source,
            ad_group=ad_group,
            source_credentials=default_settings.credentials
        )

        ad_group_source.save()

        name = 'ONE: {} / {} / {} / {} / {}'.format(
            ad_group.campaign.account.name.encode('utf-8'),
            ad_group.campaign.name.encode('utf-8'),
            ad_group.name.encode('utf-8'),
            ad_group.id,
            source.name.encode('utf-8')
        )

        actionlog.api.create_campaign(ad_group_source, name)
        self._add_to_history(ad_group_source)

        return self.create_api_response(None)

    def _add_to_history(self, ad_group_source):
        changes_text = '{} campaign created.'.format(ad_group_source.source.name)

        try:
            latest_ad_group_settings = models.AdGroupSettings.objects \
                .filter(ad_group=ad_group_source.ad_group) \
                .latest('created_dt')
        except models.AdGroupSettings.DoesNotExist:
            # there are no settings, we create the first one
            latest_ad_group_settings = models.AdGroupSettings(ad_group=ad_group_source.ad_group)

        new_ad_group_settings = latest_ad_group_settings
        new_ad_group_settings.pk = None
        new_ad_group_settings.changes_text = changes_text
        new_ad_group_settings.save()


class Account(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_put')
    def put(self, request):
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        account = models.Account(name=create_name(models.Account.objects, 'New account'))
        account.save()

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

        name = create_name(models.Campaign.objects.filter(account=account), 'New campaign')

        campaign = models.Campaign(
            name=name,
            account=account
        )
        campaign.save()

        settings = models.CampaignSettings(
            name=name,
            campaign=campaign,
            account_manager=request.user,
        )
        settings.save()

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

        settings_writer.set(resource)
        return self.create_api_response()


class AdGroupAdsPlusUpload(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_post')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.new_content_ads_tab'):
            raise exc.ForbiddenError(message='Not allowed')

        helpers.get_ad_group(request.user, ad_group_id)

        form = forms.AdGroupAdsPlusUploadForm(request.POST, request.FILES)

        if not form.is_valid():
            raise exc.ValidationError(errors=form.errors)

        batch_name = form.cleaned_data['batch_name']
        content_ads = form.cleaned_data['content_ads']

        batch = models.UploadBatch.objects.create(name=batch_name)
        ProcessUploadThread(content_ads, batch, ad_group_id).start()

        return self.create_api_response({'batch_id': batch.pk})


class AdGroupAdsPlusUploadStatus(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_status_get')
    def get(self, request, ad_group_id, batch_id):
        if not request.user.has_perm('zemauth.new_content_ads_tab'):
            raise exc.ForbiddenError(message='Not allowed')

        helpers.get_ad_group(request.user, ad_group_id)

        try:
            batch = models.UploadBatch.objects.get(pk=batch_id)
        except models.UploadBatch.DoesNotExist():
            raise exc.MissingDataException()

        response_data = {'status': batch.status}

        if batch.status == constants.UploadBatchStatus.FAILED:
            response_data['errors'] = {'content_ads': ['An error occured while processing file.']}

        return self.create_api_response(response_data)


class AdGroupContentAdState(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_content_ad_state_post')
    def post(self, request, ad_group_id, content_ad_id):
        if not request.user.has_perm('zemauth.new_content_ads_tab'):
            raise exc.ForbiddenError(message='Not allowed')

        helpers.get_ad_group(request.user, ad_group_id)

        data = json.loads(request.body)

        state = data.get('state')
        if state is None or state not in constants.ContentAdSourceState.get_all():
            raise exc.ValidationError()

        try:
            content_ad = models.ContentAd.objects.get(pk=content_ad_id)
        except models.ContentAd.DoesNotExist():
            raise exc.MissingDataException()

        for content_ad_source in content_ad.contentadsource_set.all():
            prev_state = content_ad_source.state
            content_ad_source.state = state
            content_ad_source.save()

            if prev_state != state and\
                    content_ad_source.submission_status == constants.ContentAdSubmissionStatus.APPROVED:
                actionlog.api_contentads.init_update_content_ad_action(content_ad_source)

        return self.create_api_response()


class ProcessUploadThread(BaseThread):
    def __init__(self, content_ads, batch, ad_group_id, *args, **kwargs):
        self.content_ads = content_ads
        self.batch = batch
        self.ad_group_id = ad_group_id
        super(ProcessUploadThread, self).__init__(*args, **kwargs)

    def run(self):
        content_ad_sources = []

        try:
            # ensure content ads are only commited to DB
            # if all of them are successfully processed
            with transaction.atomic():
                for ad in self.content_ads:
                    image_id = image.process_image(ad.get('image_url'), ad.get('crop_areas'))
                    content_ad = models.ContentAd.objects.create(
                        image_id=image_id,
                        batch=self.batch
                    )

                    models.Article.objects.create(
                        url=ad.get('url'),
                        title=ad.get('title'),
                        ad_group_id=self.ad_group_id,
                        content_ad=content_ad
                    )

                    for ad_group_source in models.AdGroupSource.objects.filter(ad_group_id=self.ad_group_id):
                        if not ad_group_source.source.can_manage_content_ads():
                            continue

                        content_ad_source = models.ContentAdSource.objects.create(
                            source=ad_group_source.source,
                            content_ad=content_ad,
                            submission_status=constants.ContentAdSubmissionStatus.PENDING,
                            state=constants.ContentAdSourceState.ACTIVE
                        )

                        content_ad_sources.append(content_ad_source)

                self.batch.status = constants.UploadBatchStatus.DONE
                self.batch.save()
        except Exception as e:
            self.batch.status = constants.UploadBatchStatus.FAILED
            self.batch.save()

            request_provider.delete()

            if not isinstance(e, image.ImageProcessingException):
                raise e

        for content_ad_source in content_ad_sources:
            actionlog.api_contentads.init_insert_content_ad_action(content_ad_source)

        request_provider.delete()


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
