# -*- coding: utf-8 -*-
import datetime
import json
import logging
import math
import dateutil.parser
from collections import OrderedDict
import unicodecsv
from xlwt import Workbook, Style
import slugify
import excel_styles
import base64
import httplib
import traceback
import urllib
import urllib2
import threading
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core import urlresolvers
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import render, redirect
from django.http import HttpResponse
import pytz

from utils import statsd_helper
from utils import api_common
from utils import exc
from utils import pagerduty_helper
import actionlog.api
import actionlog.sync
import actionlog.zwei_actions
import reports.api

from dash import forms
from dash import models
from dash import api

from zemauth.models import User as ZemUser

import constants

logger = logging.getLogger(__name__)

STATS_START_DELTA = 30
STATS_END_DELTA = 1


def get_ad_group(user, ad_group_id, select_related=False):
    try:
        ad_group = models.AdGroup.objects.get_for_user(user).\
            filter(id=int(ad_group_id))

        if select_related:
            ad_group = ad_group.select_related('campaign__account')

        return ad_group.get()
    except models.AdGroup.DoesNotExist:
        raise exc.MissingDataError('Ad Group does not exist')


def get_campaign(user, campaign_id):
    try:
        return models.Campaign.objects.get_for_user(user).\
            filter(id=int(campaign_id)).get()
    except models.Campaign.DoesNotExist:
        raise exc.MissingDataError('Campaign does not exist')


def get_account(user, account_id, select_related=False):
    try:
        account = models.Account.objects.get_for_user(user)
        if select_related:
            account = account.select_related('campaign_set')

        return account.filter(id=int(account_id)).get()
    except models.Account.DoesNotExist:
        raise exc.MissingDataError('Account does not exist')


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + datetime.timedelta(n)


def get_stats_start_date(start_date):
    if start_date:
        date = dateutil.parser.parse(start_date)
    else:
        date = datetime.datetime.utcnow() - datetime.timedelta(days=STATS_START_DELTA)

    return date.date()


def get_stats_end_date(end_time):
    if end_time:
        date = dateutil.parser.parse(end_time)
    else:
        date = datetime.datetime.utcnow() - datetime.timedelta(days=STATS_END_DELTA)

    return date.date()


def generate_rows(dimensions, ad_group_id, start_date, end_date):
    ordering = ['date'] if 'date' in dimensions else []
    data = reports.api.query(
        start_date,
        end_date,
        dimensions,
        ordering,
        ad_group=int(ad_group_id)
    )

    if 'source' in dimensions:
        sources = {source.id: source for source in models.Source.objects.all()}

    for item in data:
        if 'source' in dimensions:
            item['source'] = sources[item['source']].name

    return data


def write_excel_row(worksheet, row_index, column_data):
    for column_index, column_value in enumerate(column_data):
        worksheet.write(
            row_index,
            column_index,
            column_value[0],
            column_value[1] if len(column_value) > 1 else Style.default_style
        )


def create_excel_worksheet(workbook, name, widths, header_names, data, transform_func):
    worksheet = workbook.add_sheet(name)

    for index, width in widths:
        worksheet.col(index).width = width

    worksheet.panes_frozen = True

    for index, name in enumerate(header_names):
        worksheet.write(0, index, name)

    for index, item in enumerate(data):
        write_excel_row(worksheet, index + 1, transform_func(item))


def get_last_successful_source_sync_dates(ad_group):
    ag_sync = actionlog.sync.AdGroupSync(ad_group)
    result = {}
    for c in ag_sync.get_components():
        result[c.ad_group_source.source_id] = c.get_latest_success(recompute=False)
    return result


def is_sync_recent(last_sync_datetime):
    min_sync_date = datetime.datetime.utcnow() - datetime.timedelta(
        hours=settings.ACTIONLOG_RECENT_HOURS
    )

    if not last_sync_datetime:
        return None

    result = last_sync_datetime >= pytz.utc.localize(min_sync_date)

    return result


def get_campaign_url(ad_group, request):
    campaign_settings_url = request.build_absolute_uri(
        reverse('admin:dash_campaign_change', args=(ad_group.campaign.pk,)))
    campaign_settings_url = campaign_settings_url.replace('http://', 'https://')

    return campaign_settings_url


def send_ad_group_settings_change_mail_if_necessary(ad_group, user, request):
    if not settings.SEND_AD_GROUP_SETTINGS_CHANGE_MAIL:
        return

    campaign_settings = models.CampaignSettings.objects.\
        filter(campaign=ad_group.campaign).\
        order_by('-created_dt')[:1]

    if not campaign_settings or not campaign_settings[0].account_manager:
        logger.error('Could not send e-mail because there is no account manager set for campaign with id %s.', ad_group.campaign.pk)

        desc = {
            'campaign_settings_url': get_campaign_url(ad_group, request)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.ADOPS,
            incident_key='ad_group_settings_change_mail_failed',
            description='E-mail notification for ad group settings change was not sent because the campaign settings or account manager is not set.',
            details=desc,
        )
        return

    if user.pk == campaign_settings[0].account_manager.pk:
        return

    recipients = [campaign_settings[0].account_manager.email]

    subject = u'Settings change - ad group {}, campaign {}, account {}'.format(
        ad_group.name,
        ad_group.campaign.name,
        ad_group.campaign.account.name
    )

    link_url = request.build_absolute_uri('/ad_groups/{}/agency'.format(ad_group.pk))
    link_url = link_url.replace('http://', 'https://')

    body = u'''Hi account manager of {ad_group.name}

We'd like to notify you that {user.email} has made a change in the settings of the ad group {ad_group.name}, campaign {campaign.name}, account {account.name}. Please check {link_url} for details.

Yours truly,
Zemanta
    '''
    body = body.format(
        user=user,
        ad_group=ad_group,
        campaign=ad_group.campaign,
        account=ad_group.campaign.account,
        link_url=link_url
    )

    try:
        send_mail(
            subject,
            body,
            settings.AD_GROUP_SETTINGS_CHANGE_FROM_EMAIL,
            recipients,
            fail_silently=False
        )
    except Exception as e:
        logger.error('E-mail notification for ad group settings (ad group id: %d) change was not sent because an exception was raised: %s', ad_group.pk, traceback.format_exc(e))

        desc = {
            'campaign_settings_url': get_campaign_url(ad_group, request)
        }
        pagerduty_helper.trigger(
            event_type=pagerduty_helper.PagerDutyEventType.SYSOPS,
            incident_key='ad_group_settings_change_mail_failed',
            description='E-mail notification for ad group settings change was not sent because an exception was raised: {}'.format(traceback.format_exc(e)),
            details=desc,
        )


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
        ad_group_source.source.type, credentials, ad_group_source.source_campaign_key)

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
                'permissions': user.get_all_permissions_with_access_levels()
            }

        return result


class NavigationDataView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'navigation_data_view_get')
    def get(self, request):
        data = {}
        self.fetch_ad_groups(data, request.user)
        self.fetch_campaigns(data, request.user)
        self.fetch_accounts(data, request.user)

        result = []
        for account in data.values():
            account['campaigns'] = account['campaigns'].values()
            result.append(account)

        return self.create_api_response(result)

    def fetch_ad_groups(self, data, user):
        ad_groups = models.AdGroup.objects.get_for_user(user).select_related('campaign__account')

        for ad_group in ad_groups:
            campaign = ad_group.campaign
            account = campaign.account

            self.add_account_dict(data, account)

            campaigns = data[account.id]['campaigns']
            self.add_campaign_dict(campaigns, campaign)

            campaigns[campaign.id]['adGroups'].append({'id': ad_group.id, 'name': ad_group.name})

    def fetch_campaigns(self, data, user):
        campaigns = models.Campaign.objects.get_for_user(user).select_related('account')

        for campaign in campaigns:
            account = campaign.account

            self.add_account_dict(data, account)
            self.add_campaign_dict(data[account.id]['campaigns'], campaign)

    def fetch_accounts(self, data, user):
        accounts = models.Account.objects.get_for_user(user)

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


class AccountAgency(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_agency_get')
    def get(self, request, account_id):
        if not request.user.has_perm('zemauth.account_agency_view'):
            raise exc.MissingDataError()

        account = get_account(request.user, account_id)

        return self.create_api_response(self.get_response(account))

    @statsd_helper.statsd_timer('dash.api', 'account_agency_put')
    def put(self, request, account_id):
        if not request.user.has_perm('zemauth.account_agency_view'):
            raise exc.MissingDataError()

        account = get_account(request.user, account_id)

        resource = json.loads(request.body)

        form = forms.AccountAgencySettingsForm(resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        account.name = form.cleaned_data['name']
        account.save()

        return self.create_api_response(self.get_response(account))

    def get_response(self, data):
        return {
            'settings': {
                'id': data.id,
                'name': data.name
            }
        }


class CampaignAdGroups(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaigns_ad_group_put')
    def put(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_ad_groups_view'):
            raise exc.MissingDataError()

        campaign = get_campaign(request.user, campaign_id)

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


class CampaignSettings(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_settings_get')
    def get(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_settings_view'):
            raise exc.MissingDataError()

        campaign = get_campaign(request.user, campaign_id)

        campaign_settings = self.get_current_settings(campaign)

        response = {
            'settings': self.get_dict(campaign_settings, campaign),
            'account_managers': self.get_user_list(campaign_settings, 'campaign_settings_account_manager'),
            'sales_reps': self.get_user_list(campaign_settings, 'campaign_settings_sales_rep'),
            'history': self.get_history(campaign)
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'campaign_settings_put')
    def put(self, request, campaign_id):
        if not request.user.has_perm('zemauth.campaign_settings_view'):
            raise exc.MissingDataError()

        campaign = get_campaign(request.user, campaign_id)

        resource = json.loads(request.body)

        form = forms.CampaignSettingsForm(resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        self.set_campaign(campaign, form.cleaned_data)

        settings = models.CampaignSettings()
        self.set_settings(settings, campaign, form.cleaned_data)

        with transaction.atomic():
            campaign.save()
            settings.save()

        response = {
            'settings': self.get_dict(settings, campaign),
            'history': self.get_history(campaign)
        }

        return self.create_api_response(response)

    def get_history(self, campaign):
        settings = models.CampaignSettings.objects.\
            filter(campaign=campaign).\
            order_by('created_dt')

        history = []
        for i in range(0, len(settings)):
            old_settings = settings[i - 1] if i > 0 else None
            new_settings = settings[i]

            changes = old_settings.get_setting_changes(new_settings) \
                if old_settings is not None else None

            if i > 0 and not changes:
                continue

            settings_dict = self.convert_settings_to_dict(old_settings, new_settings)

            history.append({
                'datetime': new_settings.created_dt,
                'changed_by': new_settings.created_by.email,
                'changes_text': self.convert_changes_to_string(changes, settings_dict),
                'settings': settings_dict.values(),
                'show_old_settings': old_settings is not None
            })

        return history

    def format_decimal_to_percent(self, num):
        return '{:.2f}'.format(num * 100).rstrip('0').rstrip('.')

    def get_full_name_or_email(self, user):
        if user is None:
            return '/'

        result = user.get_full_name() or user.email
        return result.encode('utf-8')

    def convert_settings_to_dict(self, old_settings, new_settings):
        settings_dict = OrderedDict([
            ('name', {
                'name': 'Name',
                'value': new_settings.name.encode('utf-8')
            }),
            ('account_manager', {
                'name': 'Account Manager',
                'value': self.get_full_name_or_email(new_settings.account_manager)
            }),
            ('sales_representative', {
                'name': 'Sales Representative',
                'value': self.get_full_name_or_email(new_settings.sales_representative)
            }),
            ('service_fee', {
                'name': 'Service Fee',
                'value': self.format_decimal_to_percent(new_settings.service_fee) + '%'
            }),
            ('iab_category', {
                'name': 'IAB Category',
                'value': constants.IABCategory.get_text(new_settings.iab_category)
            }),
            ('promotion_goal', {
                'name': 'Promotion Goal',
                'value': constants.PromotionGoal.get_text(new_settings.promotion_goal)
            })
        ])

        if old_settings is not None:
            settings_dict['name']['old_value'] = old_settings.name.encode('utf-8')

            if old_settings.account_manager is not None:
                settings_dict['account_manager']['old_value'] = \
                    self.get_full_name_or_email(old_settings.account_manager)

            if old_settings.sales_representative is not None:
                settings_dict['sales_representative']['old_value'] = \
                    self.get_full_name_or_email(old_settings.sales_representative)

            settings_dict['service_fee']['old_value'] = \
                self.format_decimal_to_percent(old_settings.service_fee) + '%'

            settings_dict['iab_category']['old_value'] = \
                constants.IABCategory.get_text(old_settings.iab_category)

            settings_dict['promotion_goal']['old_value'] = \
                constants.PromotionGoal.get_text(old_settings.promotion_goal)

        return settings_dict

    def convert_changes_to_string(self, changes, settings_dict):
        if changes is None:
            return 'Created settings'

        change_strings = []

        for key in changes:
            setting = settings_dict[key]
            change_strings.append(
                '{} set to "{}"'.format(setting['name'], setting['value'])
            )

        return ', '.join(change_strings)

    def get_current_settings(self, campaign):
        settings = models.CampaignSettings.objects.\
            filter(campaign=campaign).\
            order_by('-created_dt')
        if settings:
            settings = settings[0]
        else:
            settings = models.CampaignSettings()

        return settings

    def get_dict(self, settings, campaign):
        result = {}

        if settings:
            result = {
                'id': str(campaign.pk),
                'name': campaign.name,
                'account_manager':
                    str(settings.account_manager.id)
                    if settings.account_manager is not None else None,
                'sales_representative':
                    str(settings.sales_representative.id)
                    if settings.sales_representative is not None else None,
                'service_fee': self.format_decimal_to_percent(settings.service_fee),
                'iab_category': settings.iab_category,
                'promotion_goal': settings.promotion_goal
            }

        return result

    def set_campaign(self, campaign, resource):
        campaign.name = resource['name']

    def set_settings(self, settings, campaign, resource):
        settings.campaign = campaign
        settings.name = resource['name']
        settings.account_manager = resource['account_manager']
        settings.sales_representative = resource['sales_representative']
        settings.service_fee = Decimal(resource['service_fee']) / 100
        settings.iab_category = resource['iab_category']
        settings.promotion_goal = resource['promotion_goal']

    def get_user_list(self, settings, perm_name):
        users = list(ZemUser.objects.get_users_with_perm(perm_name))

        manager = settings.account_manager
        if manager is not None and manager not in users:
            users.append(manager)

        return [{'id': str(user.id), 'name': self.get_full_name_or_email(user)} for user in users]


class AdGroupState(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_state_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('-created_dt')

        response = {
            'state': settings[0].state if settings
            else constants.AdGroupSettingsState.INACTIVE
        }

        return self.create_api_response(response)


class AdGroupSettings(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('dash.settings_view'):
            raise exc.MissingDataError()

        ad_group = get_ad_group(request.user, ad_group_id)

        settings = self.get_current_settings(ad_group)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog.api.is_waiting_for_set_actions(ad_group)
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_put')
    def put(self, request, ad_group_id):
        if not request.user.has_perm('dash.settings_view'):
            raise exc.MissingDataError()

        ad_group = get_ad_group(request.user, ad_group_id, select_related=True)

        current_settings = self.get_current_settings(ad_group)

        resource = json.loads(request.body)

        form = forms.AdGroupSettingsForm(
            current_settings, resource.get('settings', {})
            # initial=current_settings
        )
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        self.set_ad_group(ad_group, form.cleaned_data)

        settings = models.AdGroupSettings()
        self.set_settings(settings, current_settings, ad_group, form.cleaned_data)

        with transaction.atomic():
            ad_group.save()
            settings.save()

        api.order_ad_group_settings_update(ad_group, current_settings, settings)

        user = request.user
        changes = current_settings.get_setting_changes(settings)
        if changes:
            send_ad_group_settings_change_mail_if_necessary(ad_group, user, request)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog.api.is_waiting_for_set_actions(ad_group)
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
                'cpc_cc':
                    '{:.2f}'.format(settings.cpc_cc)
                    if settings.cpc_cc is not None else '',
                'daily_budget_cc':
                    '{:.2f}'.format(settings.daily_budget_cc)
                    if settings.daily_budget_cc is not None else '',
                'target_devices': settings.target_devices,
                'target_regions': settings.target_regions,
                'tracking_code': settings.tracking_code
            }

        return result

    def set_ad_group(self, ad_group, resource):
        ad_group.name = resource['name']

    def set_settings(self, settings, current_settings, ad_group, resource):
        settings.ad_group = ad_group
        settings.state = resource['state']
        settings.start_date = resource['start_date']
        settings.end_date = resource['end_date']
        settings.cpc_cc = resource['cpc_cc']
        settings.daily_budget_cc = resource['daily_budget_cc']
        settings.target_devices = resource['target_devices']
        settings.target_regions = resource['target_regions']
        settings.tracking_code = current_settings.tracking_code


class AdGroupAgency(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_agency_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_agency_tab_view'):
            raise exc.MissingDataError()

        ad_group = get_ad_group(request.user, ad_group_id)

        settings = self.get_current_settings(ad_group)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog.api.is_waiting_for_set_actions(ad_group),
            'history': self.get_history(ad_group)
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_put')
    def put(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_agency_tab_view'):
            raise exc.MissingDataError()

        ad_group = get_ad_group(request.user, ad_group_id)

        current_settings = self.get_current_settings(ad_group)

        resource = json.loads(request.body)

        form = forms.AdGroupAgencySettingsForm(resource.get('settings', {}))
        if not form.is_valid():
            raise exc.ValidationError(errors=dict(form.errors))

        settings = models.AdGroupSettings()
        self.set_settings(settings, current_settings, ad_group, form.cleaned_data)

        with transaction.atomic():
            settings.save()

        api.order_ad_group_settings_update(ad_group, current_settings, settings)

        user = request.user
        changes = current_settings.get_setting_changes(settings)
        if changes:
            send_ad_group_settings_change_mail_if_necessary(ad_group, user, request)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog.api.is_waiting_for_set_actions(ad_group),
            'history': self.get_history(ad_group)
        }

        return self.create_api_response(response)

    def get_current_settings(self, ad_group):
        settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('-created_dt')
        if settings:
            settings = settings[0]
        else:
            settings = models.AdGroupSettings()

        return settings

    def get_dict(self, settings, ad_group):
        result = {}

        if settings:
            result = {
                'id': str(ad_group.pk),
                'tracking_code': settings.tracking_code
            }

        return result

    def set_settings(self, settings, current_settings, ad_group, resource):
        settings.ad_group = ad_group
        settings.state = current_settings.state
        settings.start_date = current_settings.start_date
        settings.end_date = current_settings.end_date
        settings.cpc_cc = current_settings.cpc_cc
        settings.daily_budget_cc = current_settings.daily_budget_cc
        settings.target_devices = current_settings.target_devices
        settings.target_regions = current_settings.target_regions
        settings.tracking_code = resource['tracking_code']

    def get_history(self, ad_group):
        settings = models.AdGroupSettings.objects.\
            filter(ad_group=ad_group).\
            order_by('created_dt')

        history = []
        for i in range(0, len(settings)):
            old_settings = settings[i - 1] if i > 0 else None
            new_settings = settings[i]

            changes = old_settings.get_setting_changes(new_settings) \
                if old_settings is not None else None

            if i > 0 and not changes:
                continue

            settings_dict = self.convert_settings_to_dict(old_settings, new_settings)

            history.append({
                'datetime': new_settings.created_dt,
                'changed_by': new_settings.created_by.email,
                'changes_text': self.convert_changes_to_string(changes),
                'settings': settings_dict.values(),
                'show_old_settings': old_settings is not None
            })

        return history

    def convert_changes_to_string(self, changes):
        if changes is None:
            return 'Created settings'

        change_strings = []

        for key, value in changes.iteritems():
            prop = models.AdGroupSettings.get_human_prop_name(key)
            val = models.AdGroupSettings.get_human_value(key, value)
            change_strings.append(
                '{} set to "{}"'.format(prop, val)
            )

        return ', '.join(change_strings)

    def convert_settings_to_dict(self, old_settings, new_settings):
        settings_dict = OrderedDict()
        for field in models.AdGroupSettings._settings_fields:
            settings_dict[field] = {
                'name': models.AdGroupSettings.get_human_prop_name(field),
                'value': models.AdGroupSettings.get_human_value(field, getattr(
                    new_settings,
                    field,
                    models.AdGroupSettings.get_default_value(field)
                ))
            }

            if old_settings is not None:
                old_value = models.AdGroupSettings.get_human_value(field, getattr(
                    old_settings,
                    field,
                    models.AdGroupSettings.get_default_value(field)
                ))
                settings_dict[field]['old_value'] = old_value

        return settings_dict


class AdGroupSources(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_sources_add_source'):
            raise exc.MissingDataError()

        ad_group = get_ad_group(request.user, ad_group_id)

        sources = map(lambda s: s.source, models.DefaultSourceSettings.objects.exclude(credentials__isnull=True))
        ad_group_sources = ad_group.sources.all().order_by('name')

        sources = [{'id': s.id, 'name': s.name} for s in sources if s not in ad_group_sources]

        return self.create_api_response({
            'sources': sources,
            'sources_waiting': [source.name for source in actionlog.api.get_sources_waiting(ad_group)]
        })

    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_put')
    def put(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_sources_add_source'):
            raise exc.MissingDataError()

        ad_group = get_ad_group(request.user, ad_group_id)

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

        return self.create_api_response(None)


class AdGroupSourcesTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'zemauth.ad_group_sources_table_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        sources_data = reports.api.query(
            get_stats_start_date(request.GET.get('start_date')),
            get_stats_end_date(request.GET.get('end_date')),
            ['source'],
            ad_group=int(ad_group.id)
        )

        sources = self.get_active_ad_group_sources(ad_group)
        source_settings = models.AdGroupSourceSettings.get_current_settings(
            ad_group, sources)

        yesterday_cost = {}
        yesterday_total_cost = None
        if request.user.has_perm('reports.yesterday_spend_view'):
            yesterday_cost = reports.api.get_yesterday_cost(ad_group)
            if yesterday_cost:
                yesterday_total_cost = sum(yesterday_cost.values())

        totals_data = reports.api.query(
            get_stats_start_date(request.GET.get('start_date')),
            get_stats_end_date(request.GET.get('end_date')),
            ad_group=int(ad_group.id)
        )

        last_success_actions = get_last_successful_source_sync_dates(ad_group)

        last_sync = None
        if last_success_actions.values() and None not in last_success_actions.values():
            last_sync = pytz.utc.localize(min(last_success_actions.values()))

        return self.create_api_response({
            'rows': self.get_rows(
                ad_group,
                sources,
                sources_data,
                source_settings,
                last_success_actions,
                yesterday_cost,
                order=request.GET.get('order', None)
            ),
            'totals': self.get_totals(
                ad_group,
                totals_data,
                source_settings,
                yesterday_total_cost
            ),
            'last_sync': last_sync,
            'is_sync_recent': is_sync_recent(last_sync),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress([ad_group]),
        })

    def get_active_ad_group_sources(self, ad_group):
        sources = ad_group.sources.all().order_by('name')
        inactive_sources = actionlog.api.get_sources_waiting(ad_group)

        return [s for s in sources if s not in inactive_sources]

    def get_totals(self, ad_group, totals_data, source_settings, yesterday_cost):
        return {
            'daily_budget': float(sum(settings.daily_budget_cc for settings in source_settings.values()
                                      if settings.daily_budget_cc is not None)),
            'cost': totals_data['cost'],
            'cpc': totals_data['cpc'],
            'clicks': totals_data['clicks'],
            'impressions': totals_data['impressions'],
            'ctr': totals_data['ctr'],
            'yesterday_cost': yesterday_cost
        }

    def get_rows(self, ad_group, sources, sources_data, source_settings, last_actions, yesterday_cost, order=None):
        rows = []
        for source in sources:
            sid = source.pk
            try:
                settings = source_settings[sid]
            except KeyError:
                logger.error(
                    'Missing ad group source settings for ad group %s and source %s' %
                    (ad_group.id, sid))
                continue

            # get source reports data
            source_data = {}
            for item in sources_data:
                if item['source'] == sid:
                    source_data = item
                    break

            last_sync = last_actions.get(sid)
            if last_sync:
                last_sync = pytz.utc.localize(last_sync)

            supply_dash_url = urlresolvers.reverse('dash.views.supply_dash_redirect')
            supply_dash_url += '?ad_group_id={}&source_id={}'.format(ad_group.pk, sid)

            rows.append({
                'id': str(sid),
                'name': settings.ad_group_source.source.name,
                'status': settings.state,
                'bid_cpc': float(settings.cpc_cc) if settings.cpc_cc is not None else None,
                'daily_budget':
                    float(settings.daily_budget_cc)
                    if settings.daily_budget_cc is not None
                    else None,
                'cost': source_data.get('cost', None),
                'cpc': source_data.get('cpc', None),
                'clicks': source_data.get('clicks', None),
                'impressions': source_data.get('impressions', None),
                'ctr': source_data.get('ctr', None),
                'last_sync': last_sync,
                'yesterday_cost': yesterday_cost.get(sid),
                'supply_dash_url': supply_dash_url
            })

        if order:
            reverse = False
            if order.startswith('-'):
                reverse = True
                order = order[1:]

            # Sort should always put Nones at the end
            def _sort(item):
                value = item.get(order)
                if order == 'last_sync' and not value:
                    value = datetime.datetime(datetime.MINYEAR, 1, 1)

                return (item.get(order) is None or reverse, value)

            rows = sorted(rows, key=_sort, reverse=reverse)

        return rows


class AccountsAccountsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'accounts_accounts_table_get')
    def get(self, request):
        # Permission check
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        page = request.GET.get('page')
        size = request.GET.get('size')
        order = request.GET.get('order')
        user = request.user
        accounts = models.Account.objects.get_for_user(user)

        size = max(min(int(size or 5), 50), 1)
        if page:
            page = int(page)

        accounts_data = reports.api.query(
            get_stats_start_date(request.GET.get('start_date')),
            get_stats_end_date(request.GET.get('end_date')),
            ['account'],
            account=accounts
        )

        ad_groups_settings = models.AdGroupSettings.objects.\
            distinct('ad_group').\
            filter(ad_group__campaign__account__in=[x.pk for x in accounts]).\
            order_by('ad_group', '-created_dt')

        totals_data = reports.api.query(
            get_stats_start_date(request.GET.get('start_date')),
            get_stats_end_date(request.GET.get('end_date')),
            account=accounts
        )

        last_success_actions = {}
        for account in accounts:
            account_sync = actionlog.sync.AccountSync(account)

            if not len(list(account_sync.get_components())):
                continue

            last_success_actions[account.pk] = account_sync.get_latest_success(
                recompute=False)

        last_sync = None
        if last_success_actions.values() and None not in last_success_actions.values():
            last_sync = pytz.utc.localize(min(last_success_actions.values()))

        rows, current_page, num_pages, count, start_index, end_index = self.get_rows(
            accounts,
            accounts_data,
            ad_groups_settings,
            last_success_actions,
            page=page,
            size=size,
            order=order
        )

        return self.create_api_response({
            'rows': rows,
            'totals': self.get_totals(totals_data),
            'last_sync': last_sync,
            'is_sync_recent': is_sync_recent(last_sync),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(accounts=accounts),
            'order': order,
            'pagination': {
                'currentPage': current_page,
                'numPages': num_pages,
                'count': count,
                'startIndex': start_index,
                'endIndex': end_index,
                'size': size
            }
        })

    def get_totals(self, totals_data):
        return {
            'cost': totals_data['cost'],
            'cpc': totals_data['cpc'],
            'clicks': totals_data['clicks'],
            'impressions': totals_data['impressions'],
            'ctr': totals_data['ctr']
        }

    def get_rows(self, accounts, accounts_data, ad_groups_settings, last_actions, page, size, order=None):
        rows = []
        for account in accounts:
            aid = account.pk

            for ad_group_settings in ad_groups_settings:
                if ad_group_settings.ad_group.campaign.account.pk == aid and \
                        ad_group_settings.state == constants.AdGroupSettingsState.ACTIVE:
                    state = constants.AdGroupSettingsState.ACTIVE
                    break
            else:
                state = constants.AdGroupSettingsState.INACTIVE

            # get source reports data
            account_data = {}
            for item in accounts_data:
                if item['account'] == aid:
                    account_data = item
                    break

            last_sync = last_actions.get(aid)
            if last_sync:
                last_sync = pytz.utc.localize(last_sync)

            rows.append({
                'id': str(aid),
                'name': account.name,
                'status': state,
                'cost': account_data.get('cost', None),
                'cpc': account_data.get('cpc', None),
                'clicks': account_data.get('clicks', None),
                'last_sync': last_sync
            })

        if order:
            reverse = False
            if order.startswith('-'):
                reverse = True
                order = order[1:]

            # Sort should always put Nones at the end
            def _sort(item):
                value = item.get(order)
                if order == 'last_sync' and not value:
                    value = pytz.UTC.localize(datetime.datetime(datetime.MINYEAR, 1, 1))
                elif order == 'name':
                    value = value.lower()

                return (item.get(order) is None or reverse, value)

            rows = sorted(rows, key=_sort, reverse=reverse)

        len_accounts = len(accounts)
        current_page = page or 1
        num_pages = int(math.ceil(float(len_accounts) / size))
        count = len_accounts
        start_index = 1
        end_index = size if len_accounts > size else len_accounts

        if page and size:
            start = (page - 1) * size
            end = page * size
            if start <= len_accounts:
                rows = rows[start:end]
                start_index = start + 1
                end_index = end - (size - len(rows))
            else:
                current_page = 1

        return rows, current_page, num_pages, count, start_index, end_index


class AdGroupAdsExport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_export_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        start_date = get_stats_start_date(request.GET.get('start_date'))
        end_date = get_stats_end_date(request.GET.get('end_date'))

        filename = '{0}_{1}_detailed_report_{2}_{3}'.format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.name),
            start_date,
            end_date
        )

        ads_results = generate_rows(
            ['date', 'article'],
            ad_group.id,
            start_date,
            end_date
        )

        if request.GET.get('type') == 'excel':
            sources_results = generate_rows(
                ['date', 'source', 'article'],
                ad_group_id,
                start_date,
                end_date
            )

            return self.create_excel_response(ads_results, sources_results, filename)
        else:
            return self.create_csv_response(ads_results, filename)

    def create_csv_response(self, data, filename):
        response = self.create_file_response('text/csv; name="%s.csv"' % filename, '%s.csv' % filename)

        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('title', 'Title'),
            ('url', 'URL'),
            ('cost', 'Cost'),
            ('cpc', 'CPC'),
            ('clicks', 'Clicks'),
            ('impressions', 'Impressions'),
            ('ctr', 'CTR')
        ])

        writer = unicodecsv.DictWriter(response, fieldnames, encoding='utf-8', dialect='excel')

        # header
        writer.writerow(fieldnames)

        for item in data:
            # Format
            row = {}
            for key in ['cost', 'cpc', 'ctr']:
                val = item[key]
                if not isinstance(val, float):
                    val = 0
                row[key] = '{:.2f}'.format(val)
            for key in fieldnames:
                row[key] = item[key]

            writer.writerow(row)

        return response

    def create_excel_response(self, ads_data, sources_data, filename):
        response = self.create_file_response('application/octet-stream', '%s.xls' % filename)

        workbook = Workbook(encoding='UTF-8')

        create_excel_worksheet(
            workbook,
            'Detailed Report',
            [(1, 6000), (2, 8000), (6, 3000)],
            ['Date', 'Title', 'URL', 'Cost', 'CPC', 'Clicks', 'Impressions', 'CTR'],
            ads_data,
            lambda item: [
                (item['date'], excel_styles.style_date),
                (item['title'],),
                (item['url'],),
                (item['cost'] or 0, excel_styles.style_usd),
                (item['cpc'] or 0, excel_styles.style_usd),
                (item['clicks'] or 0,),
                (item['impressions'] or 0,),
                ((item['ctr'] or 0) / 100, excel_styles.style_percent)
            ]
        )

        create_excel_worksheet(
            workbook,
            'Per Source Report',
            [(1, 6000), (2, 8000), (3, 4000), (7, 3000)],
            ['Date', 'Title', 'URL', 'Source', 'Cost', 'CPC', 'Clicks', 'Impressions', 'CTR'],
            sources_data,
            lambda item: [
                (item['date'], excel_styles.style_date),
                (item['title'],),
                (item['url'],),
                (item['source'],),
                (item['cost'] or 0, excel_styles.style_usd),
                (item['cpc'] or 0, excel_styles.style_usd),
                (item['clicks'] or 0,),
                (item['impressions'] or 0,),
                ((item['ctr'] or 0) / 100, excel_styles.style_percent)
            ]
        )

        workbook.save(response)
        return response


class AdGroupSourcesExport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_export_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        start_date = get_stats_start_date(request.GET.get('start_date'))
        end_date = get_stats_end_date(request.GET.get('end_date'))

        filename = '{0}_{1}_per_sources_report_{2}_{3}'.format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.name),
            start_date,
            end_date
        )

        date_source_results = generate_rows(
            ['date', 'source'],
            ad_group.id,
            start_date,
            end_date
        )

        if request.GET.get('type') == 'excel':
            date_results = generate_rows(
                ['date'],
                ad_group.id,
                start_date,
                end_date
            )

            return self.create_excel_response(
                date_results,
                date_source_results,
                filename,
                request.user.has_perm('reports.per_day_sheet_source_export')
            )
        else:
            return self.create_csv_response(date_source_results, filename)

    def create_csv_response(self, data, filename):
        response = self.create_file_response('text/csv; name="%s.csv"' % filename, '%s.csv' % filename)

        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('source', 'Source'),
            ('cost', 'Cost'),
            ('cpc', 'CPC'),
            ('clicks', 'Clicks'),
            ('impressions', 'Impressions'),
            ('ctr', 'CTR')
        ])

        writer = unicodecsv.DictWriter(response, fieldnames, encoding='utf-8', dialect='excel')

        # header
        writer.writerow(fieldnames)

        for item in data:
            # Format
            row = {}
            for key in ['cost', 'cpc', 'ctr']:
                val = item[key]
                if not isinstance(val, float):
                    val = 0
                row[key] = '{:.2f}'.format(val)
            for key in fieldnames:
                row[key] = item[key]

            writer.writerow(row)

        return response

    def create_excel_response(self, date_data, date_source_data, filename, include_per_day=False):
        response = self.create_file_response('application/octet-stream', '%s.xls' % filename)

        workbook = Workbook(encoding='UTF-8')

        if include_per_day:
            create_excel_worksheet(
                workbook,
                'Per-Day Report',
                [],
                ['Date', 'Cost', 'CPC', 'Clicks', 'Impressions', 'CTR'],
                date_data,
                lambda item: [
                    (item['date'], excel_styles.style_date),
                    (item['cost'] or 0, excel_styles.style_usd),
                    (item['cpc'] or 0, excel_styles.style_usd),
                    (item['clicks'] or 0,),
                    (item['impressions'] or 0,),
                    ((item['ctr'] or 0) / 100, excel_styles.style_percent)
                ]
            )

        create_excel_worksheet(
            workbook,
            'Per-Source Report',
            [(1, 6000), (5, 3000)],
            ['Date', 'Source', 'Cost', 'CPC', 'Clicks', 'Impressions', 'CTR'],
            date_source_data,
            lambda item: [
                (item['date'], excel_styles.style_date),
                (item['source'],),
                (item['cost'] or 0, excel_styles.style_usd),
                (item['cpc'] or 0, excel_styles.style_usd),
                (item['clicks'] or 0,),
                (item['impressions'] or 0,),
                ((item['ctr'] or 0) / 100, excel_styles.style_percent)
            ]
        )

        workbook.save(response)
        return response


class TriggerAccountSyncThread(threading.Thread):
    """ Used to trigger sync for all accounts asynchronously. """
    def __init__(self, accounts, *args, **kwargs):
        self.accounts = accounts
        super(TriggerAccountSyncThread, self).__init__(*args, **kwargs)

    def run(self):
        try:
            for account in self.accounts:
                actionlog.sync.AccountSync(account).trigger_all()
        except Exception:
            logger.exception('Exception in TriggerAccountSyncThread')


class TriggerCampaignSyncThread(threading.Thread):
    """ Used to trigger sync for all campaign's ad groups asynchronously. """
    def __init__(self, campaigns, *args, **kwargs):
        self.campaigns = campaigns
        super(TriggerCampaignSyncThread, self).__init__(*args, **kwargs)

    def run(self):
        try:
            for campaign in self.campaigns:
                actionlog.sync.CampaignSync(campaign).trigger_all()
        except Exception:
            logger.exception('Exception in TriggerCampaignSyncThread')


class AccountSync(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'account_sync_get')
    def get(self, request):
        accounts = models.Account.objects.get_for_user(request.user)
        if not actionlog.api.is_sync_in_progress(accounts=accounts):
            # trigger account sync asynchronously and immediately return
            TriggerAccountSyncThread(accounts).start()

        return self.create_api_response({})


class AccountSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_is_sync_in_progress')
    def get(self, request):
        accounts = models.Account.objects.get_for_user(request.user)

        in_progress = actionlog.api.is_sync_in_progress(accounts=accounts)

        return self.create_api_response({'is_sync_in_progress': in_progress})


class CampaignSync(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'campaign_sync_get')
    def get(self, request):
        account_id = request.GET.get('account_id')
        campaign_id = request.GET.get('campaign_id')

        if account_id:
            campaigns = models.Campaign.objects.get_for_user(request.user).\
                filter(account=account_id)
        else:
            campaigns = models.Campaign.objects.get_for_user(request.user)

            if campaign_id:
                campaigns = campaigns.filter(pk=campaign_id)

        if not actionlog.api.is_sync_in_progress(campaigns=campaigns):
            # trigger account sync asynchronously and immediately return
            TriggerCampaignSyncThread(campaigns).start()

        return self.create_api_response({})


class CampaignSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_is_sync_in_progress')
    def get(self, request, campaign_id):
        account_id = request.GET.get('account_id')
        campaign_id = request.GET.get('campaign_id')

        if account_id:
            campaigns = models.Campaign.objects.get_for_user(request.user).\
                filter(account=account_id)
        else:
            campaigns = models.Campaign.objects.get_for_user(request.user)

            if campaign_id:
                campaigns = campaigns.filter(pk=campaign_id)

        in_progress = actionlog.api.is_sync_in_progress(campaigns=campaigns)

        return self.create_api_response({'is_sync_in_progress': in_progress})


class AdGroupSync(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_sync')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        if not actionlog.api.is_sync_in_progress(ad_groups=[ad_group]):
            actionlog.sync.AdGroupSync(ad_group).trigger_all()

        return self.create_api_response({})


class AdGroupCheckSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_is_sync_in_progress')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        in_progress = actionlog.api.is_sync_in_progress(ad_groups=[ad_group])

        return self.create_api_response({'is_sync_in_progress': in_progress})


class AdGroupAdsTable(api_common.BaseApiView):

    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_table_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        page = request.GET.get('page')
        size = request.GET.get('size')
        start_date = get_stats_start_date(request.GET.get('start_date'))
        end_date = get_stats_end_date(request.GET.get('end_date'))
        order = request.GET.get('order') or '-clicks'

        size = max(min(int(size or 5), 50), 1)

        result = reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['article'],
            order=[order],
            ad_group=ad_group.id
        )

        result_pg, current_page, num_pages, count, start_index, end_index = reports.api.paginate(result, page, size)

        rows = result_pg

        totals_data = reports.api.query(start_date, end_date, ad_group=int(ad_group.id))

        last_sync = actionlog.sync.AdGroupSync(ad_group).get_latest_success(
            recompute=False)
        if last_sync:
            last_sync = pytz.utc.localize(last_sync)

        return self.create_api_response({
            'rows': rows,
            'totals': totals_data,
            'last_sync': last_sync,
            'is_sync_recent': is_sync_recent(last_sync),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress([ad_group]),
            'order': order,
            'pagination': {
                'currentPage': current_page,
                'numPages': num_pages,
                'count': count,
                'startIndex': start_index,
                'endIndex': end_index,
                'size': size
            }
        })


class CampaignAdGroupsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_ad_groups_table_get')
    def get(self, request, campaign_id):
        campaign = get_campaign(request.user, campaign_id)

        start_date = get_stats_start_date(request.GET.get('start_date'))
        end_date = get_stats_end_date(request.GET.get('end_date'))
        order = request.GET.get('order') or '-cost'

        stats = reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['ad_group'],
            order=[order],
            campaign=campaign
        )

        ad_groups = campaign.adgroup_set.all()
        ad_groups_settings = models.AdGroupSettings.objects.\
            distinct('ad_group').\
            filter(ad_group__campaign=campaign).\
            order_by('ad_group', '-created_dt')

        totals_stats = reports.api.query(start_date, end_date, campaign=campaign.pk)

        last_success_actions = {}
        for ad_group in ad_groups:
            ad_group_sync = actionlog.sync.AdGroupSync(ad_group)

            if not len(list(ad_group_sync.get_components())):
                continue

            last_success_actions[ad_group.pk] = ad_group_sync.get_latest_success(
                recompute=False)

        last_sync = actionlog.sync.CampaignSync(campaign).get_latest_success(
            recompute=False)
        if last_sync:
            last_sync = pytz.utc.localize(last_sync)

        return self.create_api_response({
            'rows': self.get_rows(
                ad_groups, ad_groups_settings, stats, last_success_actions, order),
            'totals': totals_stats,
            'last_sync': last_sync,
            'is_sync_recent': is_sync_recent(last_sync),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(
                campaigns=[campaign]),
            'order': order,
        })

    def get_rows(self, ad_groups, ad_groups_settings, stats, last_actions, order):
        rows = []
        for ad_group in ad_groups:
            row = {
                'name': ad_group.name,
                'ad_group': str(ad_group.pk)
            }

            row['state'] = models.AdGroupSettings.get_default_value('state')
            for ad_group_settings in ad_groups_settings:
                if ad_group.pk == ad_group_settings.ad_group_id and \
                        ad_group_settings.state is not None:
                    row['state'] = ad_group_settings.state
                    break

            for stat in stats:
                if ad_group.pk == stat['ad_group']:
                    row.update(stat)
                    break

            last_sync = last_actions.get(ad_group.pk)
            if last_sync:
                last_sync = pytz.utc.localize(last_sync)

            row['last_sync'] = last_sync

            rows.append(row)

        if order:
            reverse = False
            if order.startswith('-'):
                reverse = True
                order = order[1:]

            # Sort should always put Nones at the end
            def _sort(item):
                value = item.get(order)
                if order == 'last_sync' and not value:
                    value = datetime.datetime(datetime.MINYEAR, 1, 1)

                return (item.get(order) is None or reverse, value)

            rows = sorted(rows, key=_sort, reverse=reverse)

        return rows


class AccountCampaignsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_campaigns_table_get')
    def get(self, request, account_id):
        user = request.user

        campaigns = models.Campaign.objects.get_for_user(user).\
            filter(account=account_id)

        start_date = get_stats_start_date(request.GET.get('start_date'))
        end_date = get_stats_end_date(request.GET.get('end_date'))
        order = request.GET.get('order') or '-clicks'

        campaign_ids = [x.pk for x in campaigns]
        stats = reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['campaign'],
            order=[order],
            campaign=campaign_ids
        )

        totals_stats = reports.api.query(start_date, end_date, campaign=campaign_ids)

        ad_groups_settings = models.AdGroupSettings.objects.\
            distinct('ad_group').\
            filter(ad_group__campaign__in=campaigns).\
            order_by('ad_group', '-created_dt')

        last_success_actions = {}
        for campaign in campaigns:
            campaign_sync = actionlog.sync.CampaignSync(campaign)

            if not len(list(campaign_sync.get_components())):
                continue

            last_success_actions[campaign.pk] = campaign_sync.get_latest_success(
                recompute=False)

        last_sync = actionlog.sync.CampaignSync(campaigns).get_latest_success(
            recompute=False)
        if last_sync:
            last_sync = pytz.utc.localize(last_sync)

        return self.create_api_response({
            'rows': self.get_rows(
                campaigns,
                ad_groups_settings,
                stats,
                last_success_actions,
                order
            ),
            'totals': totals_stats,
            'last_sync': last_sync,
            'is_sync_recent': is_sync_recent(last_sync),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(
                campaigns=campaigns),
            'order': order,
        })

    def get_rows(self, campaigns, ad_groups_settings, stats, last_actions, order):
        rows = []
        for campaign in campaigns:
            # If at least one ad group is active, then the campaign is considered
            # active.
            state = constants.AdGroupSettingsState.INACTIVE
            for ad_group_settings in ad_groups_settings:
                if ad_group_settings.ad_group.campaign.pk == campaign.pk and \
                        ad_group_settings.state == constants.AdGroupSettingsState.ACTIVE:
                    state = constants.AdGroupSettingsState.ACTIVE
                    break

            campaign_stat = {}
            for stat in stats:
                if stat['campaign'] == campaign.pk:
                    campaign_stat = stat
                    break

            last_sync = last_actions.get(campaign.pk)
            if last_sync:
                last_sync = pytz.utc.localize(last_sync)

            row = {
                'campaign': str(campaign.pk),
                'name': campaign.name,
                'state': state,
                'last_sync': last_sync
            }
            row.update(campaign_stat)
            rows.append(row)

        if order:
            reverse = False
            if order.startswith('-'):
                reverse = True
                order = order[1:]

            # Sort should always put Nones at the end
            def _sort(item):
                value = item.get(order)
                if order == 'last_sync' and not value:
                    value = datetime.datetime(datetime.MINYEAR, 1, 1)

                return (item.get(order) is None or reverse, value)

            rows = sorted(rows, key=_sort, reverse=reverse)

        return rows


class AdGroupDailyStats(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_daily_stats_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        source_ids = request.GET.getlist('source_ids')
        totals = request.GET.get('totals')

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        breakdown = ['date']

        totals_stats = []
        if totals:
            totals_stats = reports.api.query(
                get_stats_start_date(start_date),
                get_stats_end_date(end_date),
                breakdown,
                ['date'],
                ad_group=int(ad_group.id)
            )

        sources = None
        breakdown_stats = []
        extra_kwargs = {}

        if source_ids:
            ids = [int(x) for x in source_ids]
            extra_kwargs['source_id'] = ids
            breakdown.append('source')
            sources = models.Source.objects.filter(pk__in=ids)

            breakdown_stats = reports.api.query(
                get_stats_start_date(start_date),
                get_stats_end_date(end_date),
                breakdown,
                ['date'],
                ad_group=int(ad_group.id),
                **extra_kwargs
            )

        return self.create_api_response(self.get_response_dict(breakdown_stats + totals_stats, sources))

    def get_response_dict(self, stats, sources):
        sources_dict = {}
        if sources:
            sources_dict = {x.pk: x.name for x in sources}

        options_dict = {}
        results = []
        for stat in stats:
            result = {
                'date': stat['date'],
                'clicks': stat['clicks'],
                'impressions': stat['impressions'],
                'ctr': round(stat['ctr'], 2)
                       if 'ctr' in stat and stat['ctr'] is not None else None,
                'cpc': round(stat['cpc'], 3)
                       if 'cpc' in stat and stat['cpc'] is not None else None,
                'cost': round(stat['cost'], 2)
                       if 'cost' in stat and stat['cost'] is not None else None
            }

            if 'source' in stat:
                result['source_id'] = stat['source']
                result['source_name'] = sources_dict[stat['source']]

            if 'goals' in stat and stat['goals'] is not None:
                for goal_name, goal_metrics in stat['goals'].items():
                    for metric_key, metric_value in goal_metrics.items():
                        metric_format = None
                        if metric_key == 'conversion_rate':
                            metric_value = round(metric_value, 2) if metric_value is not None else None
                            metric_format = 'percent'
                            metric_name = 'Conversion Rate'
                        elif metric_key == 'conversions':
                            metric_name = 'Conversions'
                        else:
                            # unknown metric
                            continue

                        metric_id = '{}_{}'.format(
                            slugify.slugify(goal_name).encode('ascii', 'ignore'),
                            metric_key
                        )

                        if metric_id not in options_dict:
                            options_dict[metric_id] = {
                                'name': '{}: {}'.format(goal_name, metric_name),
                                'value': metric_id,
                                'format': metric_format
                            }

                        result[metric_id] = metric_value

            results.append(result)

        return {
            'stats': results,
            'options': options_dict.values()
        }


class BaseDailyStatsView(api_common.BaseApiView):
    def get_stats(self, request, totals_kwargs, selected_kwargs, group_key):
        start_date = get_stats_start_date(request.GET.get('start_date'))
        end_date = get_stats_end_date(request.GET.get('end_date'))

        breakdown = ['date']

        totals_stats = []
        if totals_kwargs:
            totals_stats = reports.api.query(
                start_date,
                end_date,
                breakdown,
                ['date'],
                **totals_kwargs
            )

        breakdown_stats = []

        if selected_kwargs:
            breakdown.append(group_key)
            breakdown_stats = reports.api.query(
                start_date,
                end_date,
                breakdown,
                ['date'],
                **selected_kwargs
            )

        return breakdown_stats + totals_stats

    def get_series_groups_dict(self, totals, groups_dict):
        result = {key: {
            'id': key,
            'name': groups_dict[key],
            'series_data': {}
        } for key in groups_dict}

        if totals:
            result['totals'] = {
                'id': 'totals',
                'name': 'Totals',
                'series_data': {}
            }

        return result

    def process_stat_goals(self, stat_goals, goals, stat):
        # may modify goal_metrics and stat
        for goal_name, goal_metrics in stat_goals.items():
            for metric_type, metric_value in goal_metrics.items():
                metric_id = '{}_goal_{}'.format(
                    slugify.slugify(goal_name).encode('ascii', 'replace'),
                    metric_type
                )

                if metric_id not in goal_metrics:
                    goals[metric_id] = {
                        'name': goal_name,
                        'type': metric_type
                    }

                # set it in stat
                stat[metric_id] = metric_value

    def get_response_dict(self, stats, totals, groups_dict, metrics, group_key):
        series_groups = self.get_series_groups_dict(totals, groups_dict)
        goals = {}

        for stat in stats:
            if stat.get('goals') is not None:
                self.process_stat_goals(stat['goals'], goals, stat)

            # get id of group it belongs to
            group_id = stat.get(group_key) or 'totals'

            data = series_groups[group_id]['series_data']
            for metric in metrics:
                if metric not in data:
                    data[metric] = []

                series_groups[group_id]['series_data'][metric].append(
                    (stat['date'], stat.get(metric))
                )

        return {
            'goals': goals,
            'chart_data': series_groups.values()
        }


class CampaignDailyStats(BaseDailyStatsView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_daily_stats_get')
    def get(self, request, campaign_id):
        campaign = get_campaign(request.user, campaign_id)

        metrics = request.GET.getlist('metrics')
        selected_ids = request.GET.getlist('selected_ids')
        totals = request.GET.get('totals')

        totals_kwargs = None
        selected_kwargs = None
        ad_groups = []

        if totals:
            totals_kwargs = {'campaign': int(campaign.id)}

        if selected_ids:
            ids = [int(x) for x in selected_ids]
            selected_kwargs = {'campaign': int(campaign.id), 'ad_group_id': ids}

            ad_groups = models.AdGroup.objects.filter(pk__in=ids)

        stats = self.get_stats(request, totals_kwargs, selected_kwargs, 'ad_group')

        return self.create_api_response(self.get_response_dict(
            stats,
            totals,
            {ad_group.id: ad_group.name for ad_group in ad_groups},
            metrics,
            'ad_group'
        ))


class AccountDailyStats(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'accounts_daily_stats_get')
    def get(self, request):
        # Permission check
        if not request.user.has_perm('zemauth.all_accounts_accounts_view'):
            raise exc.MissingDataError()

        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        user = request.user

        breakdown = ['date']
        accounts = models.Account.objects.get_for_user(user)
        totals_stats = reports.api.query(
            get_stats_start_date(start_date),
            get_stats_end_date(end_date),
            breakdown,
            ['date'],
            account=accounts
        )

        return self.create_api_response({
            'stats': self.get_dict(totals_stats)
        })

    def get_dict(self, stats):
        sources_dict = {}
        for stat in stats:
            if 'source' in stat:
                stat['source_name'] = sources_dict[stat['source']]

        return stats


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

        account = get_account(request.user, account_id)

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
        'state': urllib.quote(json.dumps(state))
    }

    url = settings.SOURCE_OAUTH_URIS[source_name]['auth_uri'] + '?' + urllib.urlencode(params)
    return redirect(url)


def oauth_redirect(request, source_name):
    # Token requests are implemented using urllib2 requests because Yahoo only supports credentials in
    # Authorization header while oauth2client sends it in reqeust body (for get_token calls, after that
    # it puts access token into header).

    code = request.GET.get('code')
    state = request.GET.get('state')

    if not state or 'credentials_id' not in state:
        logger.error('Missing state in OAuth2 redirect')
        return redirect('index')

    try:
        state = json.loads(state)
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
