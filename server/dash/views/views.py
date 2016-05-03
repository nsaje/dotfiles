# -*- coding: utf-8 -*-
import calendar
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
import threading

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

import influx

from dash.views import helpers

from utils import lc_helper
from utils import statsd_helper
from utils import api_common
from utils import exc
from utils import s3helpers
from utils import email_helper

from automation import autopilot_plus

import actionlog.api
import actionlog.api_contentads
import actionlog.sync
import actionlog.zwei_actions
import actionlog.models
import actionlog.constants

from automation import campaign_stop

from dash import models, region_targeting_helper, retargeting_helper
from dash import constants
from dash import api
from dash import forms
from dash import upload
from dash import infobox_helpers
from dash import publisher_helpers

import reports.api_publishers
import reports.api

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

    @influx.timer('dash.api')
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
                    datetime.datetime.utcnow(), is_dst=True).total_seconds()
            }

        return result


@login_required
@require_GET
def demo_mode(request):
    demo_user = authenticate(username=settings.DEMO_USER_EMAIL, password=settings.DEMO_USER_PASSWORD)
    login(request, demo_user)
    return redirect('index')


class AccountArchive(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'account_archive_post')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        account.archive(request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.ARCHIVE_RESTORE_ACCOUNT, account=account)

        return self.create_api_response({})


class AccountRestore(api_common.BaseApiView):

    @influx.timer('dash.api')
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

    @influx.timer('dash.api')
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

    @influx.timer('dash.api')
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


class AdGroupOverview(api_common.BaseApiView):

    class AsyncQuery(threading.Thread):

        def __init__(self, user, ad_group):
            super(AdGroupOverview.AsyncQuery, self).__init__()
            self.user = user
            self.ad_group = ad_group
            self.yesterday_cost = None

        def run(self):
            self.yesterday_cost = infobox_helpers.get_yesterday_adgroup_spend(
                self.user,
                self.ad_group
            ) or 0

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'ad_group_overview')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        async_perf_query = AdGroupOverview.AsyncQuery(request.user, ad_group)
        async_perf_query.start()

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        ad_group_settings = ad_group.get_current_settings()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        header = {
            'title': ad_group.name,
            'active': infobox_helpers.get_adgroup_running_status(ad_group_settings, filtered_sources),
            'level': constants.InfoboxLevel.ADGROUP,
            'level_verbose': '{}: '.format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.ADGROUP)),
        }

        basic_settings, daily_cap = self._basic_settings(request.user, ad_group, ad_group_settings)
        performance_settings, is_delivering = self._performance_settings(
            ad_group, request.user, ad_group_settings, start_date, end_date,
            daily_cap, async_perf_query
        )
        for setting in performance_settings[1:]:
            setting['section_start'] = True

        response = {
            'header': header,
            'basic_settings': basic_settings,
            'performance_settings': performance_settings,
        }
        return self.create_api_response(response)

    def _basic_settings(self, user, ad_group, ad_group_settings):
        settings = []
        flight_time, flight_time_left_days =\
            infobox_helpers.format_flight_time(
                ad_group_settings.start_date,
                ad_group_settings.end_date
            )
        days_left_description = None
        if flight_time_left_days is not None:
            days_left_description = "{} days left".format(flight_time_left_days)
        flight_time_setting = infobox_helpers.OverviewSetting(
            'Flight time:',
            flight_time,
            days_left_description
        )
        settings.append(flight_time_setting.as_dict())

        max_cpc_setting = infobox_helpers.OverviewSetting(
            'Maximum CPC:',
            lc_helper.default_currency(
                ad_group_settings.cpc_cc,
                3,
            ) if ad_group_settings.cpc_cc is not None else 'No limit',
        )
        settings.append(max_cpc_setting.as_dict())

        campaign_settings = ad_group.campaign.get_current_settings()
        campaign_target_devices = campaign_settings.target_devices

        if set(campaign_target_devices) == set(ad_group_settings.target_devices):
            target_device_warning = None
        else:
            target_device_warning = 'Different than campaign default'

        targeting_device = infobox_helpers.OverviewSetting(
            'Targeting:',
            'Device: {devices}'.format(
                devices=', '.join(
                    [w[0].upper() + w[1:] for w in ad_group_settings.target_devices]
                )
            ),
            warning=target_device_warning,
            section_start=True
        )
        settings.append(targeting_device.as_dict())

        campaign_target_regions = campaign_settings.target_regions
        if set(campaign_target_regions) == set(ad_group_settings.target_regions):
            region_warning = None
        else:
            region_warning = 'Different than campaign default'

        targeting_region_setting = infobox_helpers.create_region_setting(
            ad_group_settings.target_regions
        )
        targeting_region_setting.warning = region_warning
        settings.append(targeting_region_setting.as_dict())

        tracking_code_settings = infobox_helpers.OverviewSetting(
            'Tracking codes:',
            'Yes' if ad_group_settings.tracking_code else 'No',
            section_start=True
        )
        if ad_group_settings.tracking_code:
            tracking_code_settings = tracking_code_settings.comment(
                'Show codes',
                'Hide codes',
                ad_group_settings.tracking_code
            )
        settings.append(tracking_code_settings.as_dict())

        post_click_tracking = []
        if ad_group_settings.enable_ga_tracking:
            post_click_tracking.append('Google Analytics')
        if ad_group_settings.enable_adobe_tracking:
            post_click_tracking.append('Adobe')

        if post_click_tracking == []:
            post_click_tracking.append("N/A")

        post_click_tracking_setting = infobox_helpers.OverviewSetting(
            'Post click tracking:',
            ', '.join(post_click_tracking),
        )
        settings.append(post_click_tracking_setting.as_dict())

        daily_cap = infobox_helpers.calculate_daily_ad_group_cap(ad_group)
        daily_cap_setting = infobox_helpers.OverviewSetting(
            'Daily budget:',
            lc_helper.default_currency(daily_cap) if daily_cap is not None else '',
            tooltip='Daily media budget'
        )
        settings.append(daily_cap_setting.as_dict())

        campaign_budget_setting = infobox_helpers.create_total_campaign_budget_setting(user, ad_group.campaign)
        settings.append(campaign_budget_setting.as_dict())

        if user.has_perm('zemauth.can_view_retargeting_settings'):
            retargeted_adgroup_names = list(models.AdGroup.objects.filter(
                id__in=ad_group_settings.retargeting_ad_groups
            ).values_list('name', flat=True))
            retargetings_setting = infobox_helpers.OverviewSetting(
                'Retargeting:',
                'Yes' if retargeted_adgroup_names != [] else 'No',
                tooltip='Content ads will only be shown to people who have already seen an ad from selected ad groups.'
            )
            if retargeted_adgroup_names != []:
                retargetings_setting = retargetings_setting.comment(
                    'Show Ad Groups',
                    'Hide Ad Groups',
                    ', '.join(retargeted_adgroup_names)
                )
            settings.append(retargetings_setting.as_dict())

        return settings, daily_cap

    def _performance_settings(self, ad_group, user, ad_group_settings, start_date, end_date,
                              daily_cap, async_query):
        settings = []
        common_settings, is_delivering = infobox_helpers.goals_and_spend_settings(
            user, ad_group.campaign
        )

        async_query.join()
        yesterday_cost = async_query.yesterday_cost

        settings.append(infobox_helpers.create_yesterday_spend_setting(
            yesterday_cost,
            daily_cap
        ).as_dict())
        settings.extend(common_settings)

        if user.has_perm('zemauth.campaign_goal_performance'):
            settings.extend(infobox_helpers.get_campaign_goal_list(user, {'ad_group': ad_group},
                                                                   start_date, end_date))

        return settings, is_delivering


class AdGroupArchive(api_common.BaseApiView):

    @influx.timer('dash.api')
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

    @influx.timer('dash.api')
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

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'campaigns_ad_group_put')
    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        ad_group, ad_group_settings, actions = self._create_ad_group(campaign, request)
        ad_group_settings.save(request)

        api.update_ad_group_redirector_settings(ad_group, ad_group_settings)
        actionlog.zwei_actions.send(actions)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.CREATE_AD_GROUP,
                                            ad_group=ad_group, campaign=campaign)

        response = {
            'name': ad_group.name,
            'id': ad_group.id,
        }

        return self.create_api_response(response)

    def _create_ad_group(self, campaign, request):
        actions = []
        with transaction.atomic():
            ad_group = models.AdGroup(
                name=create_name(models.AdGroup.objects.filter(campaign=campaign), 'New ad group'),
                campaign=campaign
            )
            ad_group.save(request)
            ad_group_settings = self._create_new_settings(ad_group, request)
            if request.user.has_perm('zemauth.add_media_sources_automatically'):
                media_sources_actions = self._add_media_sources(ad_group, ad_group_settings, request)
                actions.extend(media_sources_actions)

        return ad_group, ad_group_settings, actions

    def _create_new_settings(self, ad_group, request):
        current_settings = ad_group.get_current_settings()  # get default ad group settings
        new_settings = current_settings.copy_settings()
        campaign_settings = ad_group.campaign.get_current_settings()

        new_settings.target_devices = campaign_settings.target_devices
        new_settings.target_regions = campaign_settings.target_regions
        return new_settings

    def _add_media_sources(self, ad_group, ad_group_settings, request):
        sources = ad_group.campaign.account.allowed_sources.all()
        actions = []
        added_sources = []
        for source in sources:
            try:
                source_default_settings = helpers.get_source_default_settings(source)
            except exc.MissingDataError:
                logger.exception('Exception occurred on campaign with id %s', ad_group.campaign.pk)
                continue

            ad_group_source = self._create_ad_group_source(request, source_default_settings, ad_group_settings)
            external_name = ad_group_source.get_external_name()
            action = actionlog.api.create_campaign(ad_group_source, external_name, request, send=False)
            added_sources.append(source)
            actions.append(action)

        if added_sources:
            changes_text = 'Created settings and automatically created campaigns for {} sources ({})'.format(
                len(added_sources), ', '.join([source.name for source in added_sources]))
            ad_group_settings.changes_text = changes_text

        return actions

    def _create_ad_group_source(self, request, source_settings, ad_group_settings):
        ad_group = ad_group_settings.ad_group

        ad_group_source = helpers.add_source_to_ad_group(source_settings, ad_group)
        ad_group_source.save(request)
        helpers.set_ad_group_source_settings(request, ad_group_source, mobile_only=ad_group_settings.is_mobile_only())

        return ad_group_source


class CampaignOverview(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'campaign_overview')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign_settings = campaign.get_current_settings()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        header = {
            'title': campaign.name,
            'active': infobox_helpers.get_campaign_running_status(campaign),
            'level': constants.InfoboxLevel.CAMPAIGN,
            'level_verbose': '{}: '.format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.CAMPAIGN)),
        }

        basic_settings, daily_cap =\
            self._basic_settings(request.user, campaign, campaign_settings)

        performance_settings, is_delivering = self._performance_settings(
            campaign,
            request.user,
            campaign_settings,
            daily_cap,
            start_date,
            end_date,
        )

        for setting in performance_settings[1:]:
            setting['section_start'] = True

        response = {
            'header': header,
            'basic_settings': basic_settings,
            'performance_settings': performance_settings,
        }
        return self.create_api_response(response)

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'campaign_overview_basic')
    def _basic_settings(self, user, campaign, campaign_settings):
        settings = []

        count_adgroups = infobox_helpers.count_active_adgroups(campaign)
        count_adgroups_setting = infobox_helpers.OverviewSetting(
            'Active ad groups:',
            '{}'.format(count_adgroups),
            tooltip='Number of active ad groups'
        )
        settings.append(count_adgroups_setting.as_dict())

        campaign_manager_setting = infobox_helpers.OverviewSetting(
            'Campaign Manager:',
            infobox_helpers.format_username(campaign_settings.campaign_manager)
        )
        settings.append(campaign_manager_setting.as_dict())

        daily_cap_value = infobox_helpers.calculate_daily_campaign_cap(campaign)

        start_date, end_date, never_finishes = self._calculate_flight_dates(
            campaign
        )
        if never_finishes:
            end_date = None

        flight_time, flight_time_left_days =\
            infobox_helpers.format_flight_time(
                start_date,
                end_date
            )
        flight_time_left_description = None
        if flight_time_left_days is not None:
            flight_time_left_description = "{} days left".format(flight_time_left_days)
        flight_time_setting = infobox_helpers.OverviewSetting(
            'Flight time:',
            flight_time,
            flight_time_left_description
        )
        settings.append(flight_time_setting.as_dict())

        targeting_device = infobox_helpers.OverviewSetting(
            'Targeting defaults:',
            'Device: {devices}'.format(
                devices=', '.join(
                    [w[0].upper() + w[1:] for w in campaign_settings.target_devices]
                )
            ),
            section_start=True
        )
        settings.append(targeting_device.as_dict())

        targeting_region_setting = infobox_helpers.create_region_setting(
            campaign_settings.target_regions
        )
        settings.append(targeting_region_setting.as_dict())

        # take the num
        daily_cap = infobox_helpers.OverviewSetting(
            'Daily budget:',
            lc_helper.default_currency(daily_cap_value) if daily_cap_value > 0 else 'N/A',
            tooltip="Daily media budget",
            section_start=True
        )
        settings.append(daily_cap.as_dict())

        campaign_budget_setting = infobox_helpers.create_total_campaign_budget_setting(user, campaign)
        settings.append(campaign_budget_setting.as_dict())

        return settings, daily_cap_value

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'campaign_overview_performance')
    def _performance_settings(self, campaign, user, campaign_settings, daily_cap_cc,
                              start_date, end_date):
        settings = []

        yesterday_cost = infobox_helpers.get_yesterday_campaign_spend(user, campaign) or 0

        settings.append(infobox_helpers.create_yesterday_spend_setting(
            yesterday_cost,
            daily_cap_cc
        ).as_dict())

        common_settings, is_delivering = infobox_helpers.goals_and_spend_settings(
            user, campaign
        )
        settings.extend(common_settings)

        if user.has_perm('zemauth.campaign_goal_performance'):
            settings.extend(infobox_helpers.get_campaign_goal_list(user, {'campaign': campaign},
                                                                   start_date, end_date))

        return settings, is_delivering

    def _calculate_flight_dates(self, campaign):
        start_date = None
        end_date = None
        never_finishes = False

        ad_groups_settings = models.AdGroupSettings.objects.filter(
            ad_group__campaign=campaign
        ).group_current_settings().values_list('start_date', 'end_date')
        for ad_group_settings in ad_groups_settings:
            adg_start_date = ad_group_settings[0]
            adg_end_date = ad_group_settings[1]

            if start_date is None:
                start_date = adg_start_date
            else:
                start_date = min(start_date, adg_start_date)

            if adg_end_date is None:
                never_finishes = True

            if end_date is None:
                end_date = adg_end_date
            else:
                end_date = max(end_date, adg_end_date or end_date)

        return start_date, end_date, never_finishes


class AccountOverview(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'account_overview')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)

        header = {
            'title': account.name,
            'active': infobox_helpers.get_account_running_status(account),
            'level': constants.InfoboxLevel.ACCOUNT,
            'level_verbose': '{}: '.format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.ACCOUNT)),
        }

        basic_settings = self._basic_settings(account)

        performance_settings = self._performance_settings(account, request.user)
        for setting in performance_settings[1:]:
            setting['section_start'] = True

        response = {
            'header': header,
            'basic_settings': basic_settings,
            'performance_settings': performance_settings,
        }

        return self.create_api_response(response)

    def _basic_settings(self, account):
        settings = []

        count_campaigns = infobox_helpers.count_active_campaigns(account)
        count_campaigns_setting = infobox_helpers.OverviewSetting(
            'Active campaigns:',
            '{}'.format(count_campaigns),
            tooltip='Number of campaigns with at least one ad group running'
        )
        settings.append(count_campaigns_setting.as_dict())

        account_settings = account.get_current_settings()
        account_manager_setting = infobox_helpers.OverviewSetting(
            'Account Manager:',
            infobox_helpers.format_username(account_settings.default_account_manager)
        )
        settings.append(account_manager_setting.as_dict())

        sales_manager_setting = infobox_helpers.OverviewSetting(
            'Sales Rep.:',
            infobox_helpers.format_username(account_settings.default_sales_representative),
            tooltip='Sales Representative'
        )
        settings.append(sales_manager_setting.as_dict())

        all_users = account.users.all()
        if all_users.count() == 0:
            user_setting = infobox_helpers.OverviewSetting(
                'Users:',
                section_start=True,
            )
            settings.append(user_setting.as_dict())
        else:
            user_blob = '<br />'.join([infobox_helpers.format_username(u) for u in all_users])
            users_setting = infobox_helpers.OverviewSetting(
                'Users:',
                '{}'.format(all_users.count()),
                section_start=True,
                tooltip='Users assigned to this account'
            ).comment(
                'Show more',
                'Show less',
                user_blob
            )
            settings.append(users_setting.as_dict())

        pixels = models.ConversionPixel.objects.filter(account=account)
        conversion_pixel_setting = infobox_helpers.OverviewSetting(
            'Conversion pixel:',
            'Yes' if pixels.count() > 0 else 'No'
        )
        if pixels.count() > 0:
            slugs = [pixel.slug for pixel in pixels]
            conversion_pixel_setting = conversion_pixel_setting.comment(
                'Show more',
                'Show less',
                ', '.join(slugs),
            )
        settings.append(conversion_pixel_setting.as_dict())

        allocated_credit, available_credit =\
            infobox_helpers.calculate_allocated_and_available_credit(account)

        allocated_credit_setting = infobox_helpers.OverviewSetting(
            'Allocated credit:',
            lc_helper.default_currency(allocated_credit),
            description='{} unallocated'.format(lc_helper.default_currency(
                available_credit
            )),
            tooltip='Total allocated and unallocated credit',
        )
        settings.append(allocated_credit_setting.as_dict())

        return settings

    def _performance_settings(self, account, user):
        settings = []

        spent_budget, available_budget = \
            infobox_helpers.calculate_spend_and_available_budget(account)
        spent_credit_setting = infobox_helpers.OverviewSetting(
            'Spent budget:',
            lc_helper.default_currency(spent_budget),
            description='{} remaining'.format(
                lc_helper.default_currency(available_budget)
            ),
            tooltip='Spent and remaining media budget'
        )
        settings.append(spent_credit_setting.as_dict())

        daily_budget = infobox_helpers.calculate_daily_account_cap(account)
        yesterday_spent = infobox_helpers.calculate_yesterday_account_spend(account)
        settings.append(
            infobox_helpers.create_yesterday_spend_setting(
                yesterday_spent,
                daily_budget
            ).as_dict(),
        )

        return settings


class AvailableSources(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'available_sources_get')
    def get(self, request):
        show_archived = request.GET.get('show_archived') == 'true'
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

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_sources_add_source'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group_settings = ad_group.get_current_settings()

        if ad_group.is_demo:
            real_ad_groups = models.DemoAdGroupRealAdGroup.objects.filter(demo_ad_group=ad_group)
            if real_ad_groups:
                ad_group = real_ad_groups[0].real_ad_group

        allowed_sources = ad_group.campaign.account.allowed_sources.all()
        ad_group_sources = ad_group.sources.all()
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        sources_with_credentials = models.DefaultSourceSettings.objects.all().with_credentials().values('source')
        available_sources = allowed_sources.\
            exclude(pk__in=ad_group_sources).\
            filter(pk__in=filtered_sources).\
            filter(pk__in=sources_with_credentials).\
            order_by('name')

        sources = []
        for source in available_sources:
            sources.append({
                'id': source.id,
                'name': source.name,
                'can_target_existing_regions': region_targeting_helper.can_target_existing_regions(
                    source, ad_group_settings),
                'can_retarget': retargeting_helper.can_add_source_with_retargeting(source, ad_group_settings)
            })

        sources_waiting = set([ad_group_source.source.name for ad_group_source
                               in actionlog.api.get_ad_group_sources_waiting(ad_group=ad_group)])

        return self.create_api_response({
            'sources': sorted(sources, key=lambda source: source['name']),
            'sources_waiting': list(sources_waiting),
        })

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_put')
    def put(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_sources_add_source'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group_settings = ad_group.get_current_settings()

        source_id = json.loads(request.body)['source_id']
        source = models.Source.objects.get(id=source_id)

        if models.AdGroupSource.objects.filter(source=source, ad_group=ad_group).exists():
            raise exc.ValidationError(
                '{} media source for ad group {} already exists.'.format(source.name, ad_group_id))

        if not region_targeting_helper.can_target_existing_regions(source, ad_group_settings):
            raise exc.ValidationError('{} media source can not be added because it does not support selected region targeting.'
                                      .format(source.name))

        if not retargeting_helper.can_add_source_with_retargeting(source, ad_group_settings):
            raise exc.ValidationError('{} media source can not be added because it does not support retargeting.'
                                      .format(source.name))

        default_settings = helpers.get_source_default_settings(source)
        ad_group_source = helpers.add_source_to_ad_group(default_settings, ad_group)
        ad_group_source.save(request)

        external_name = ad_group_source.get_external_name()
        actionlog.api.create_campaign(ad_group_source, external_name, request)
        self._add_to_history(ad_group_source, request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.CREATE_MEDIA_SOURCE_CAMPAIGN,
                                            ad_group=ad_group)

        if request.user.has_perm('zemauth.add_media_sources_automatically'):
            helpers.set_ad_group_source_settings(
                request, ad_group_source, mobile_only=ad_group.get_current_settings().is_mobile_only())

        return self.create_api_response(None)

    def _add_to_history(self, ad_group_source, request):
        changes_text = '{} campaign created.'.format(ad_group_source.source.name)

        settings = ad_group_source.ad_group.get_current_settings().copy_settings()
        settings.changes_text = changes_text
        settings.save(request)


class Account(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'account_put')
    def put(self, request):
        if not request.user.has_perm('zemauth.all_accounts_accounts_add_account'):
            raise exc.MissingDataError()

        account = models.Account(name=create_name(models.Account.objects, 'New account'))

        if request.user.has_perm('zemauth.can_manage_agency'):
            managed_agency = models.Agency.objects.all().filter(
                users=request.user
            ).first()
            if managed_agency is not None:
                account.agency = managed_agency

        account.save(request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.CREATE_ACCOUNT, account=account)

        response = {
            'name': account.name,
            'id': account.id
        }

        return self.create_api_response(response)


class AccountCampaigns(api_common.BaseApiView):

    @influx.timer('dash.api')
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

        settings = campaign.get_current_settings()  # creates new settings with default values
        settings.name = name
        settings.campaign_manager = (account_settings.default_account_manager
                                     if account_settings.default_account_manager else request.user)
        settings.save(request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.CREATE_CAMPAIGN,
                                            campaign=campaign)

        response = {
            'name': campaign.name,
            'id': campaign.id
        }

        return self.create_api_response(response)


class AdGroupSourceSettings(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'ad_group_source_settings_put')
    def put(self, request, ad_group_id, source_id):
        resource = json.loads(request.body)
        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)

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

        if ad_group.campaign.is_in_landing():
            for key in resource.keys():
                errors.update({key: 'Not allowed'})

        ad_group_settings = ad_group.get_current_settings()
        source = models.Source.objects.get(pk=source_id)
        if 'state' in resource and state_form.cleaned_data.get('state') == constants.AdGroupSettingsState.ACTIVE and\
                not retargeting_helper.can_add_source_with_retargeting(source, ad_group_settings):
            errors.update(
                {
                    'state': 'Cannot enable media source that does not support'
                    'retargeting on adgroup with retargeting enabled.'
                }
            )

        campaign_settings = ad_group.campaign.get_current_settings()
        if 'daily_budget_cc' in resource and campaign_settings.automatic_campaign_stop:
            max_daily_budget = campaign_stop.get_max_settable_daily_budget(ad_group_source)
            if decimal.Decimal(resource['daily_budget_cc']) > max_daily_budget:
                errors.update({
                    'daily_budget_cc': [
                        'Daily budget is too high. Maximum daily budget can be up to ${max_daily_budget}.'.format(
                            max_daily_budget=max_daily_budget
                        )
                    ]
                })

        if errors:
            raise exc.ValidationError(errors=errors)

        if 'cpc_cc' in resource:
            resource['cpc_cc'] = decimal.Decimal(resource['cpc_cc'])
        if 'daily_budget_cc' in resource:
            resource['daily_budget_cc'] = decimal.Decimal(resource['daily_budget_cc'])

        if 'cpc_cc' in resource or 'daily_budget_cc' in resource:
            end_datetime = ad_group_settings.get_utc_end_datetime()
            if end_datetime is not None and end_datetime <= datetime.datetime.utcnow():
                raise exc.ValidationError()

        allowed_sources = {source.id for source in ad_group.campaign.account.allowed_sources.all()}

        settings_writer.set(resource, request)

        helpers.log_useraction_if_necessary(request, constants.UserActionType.SET_MEDIA_SOURCE_SETTINGS,
                                            ad_group=ad_group)

        autopilot_changed_sources_text = ''
        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        if ad_group_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET and\
                'state' in resource:
            changed_sources = autopilot_plus.initialize_budget_autopilot_on_ad_group(ad_group, send_mail=False)
            autopilot_changed_sources_text = ', '.join([s.source.name for s in changed_sources])

        return self.create_api_response({
            'editable_fields': helpers.get_editable_fields(
                ad_group,
                ad_group_source,
                ad_group_settings,
                ad_group_source.get_current_settings_or_none(),
                request.user,
                allowed_sources
            ),
            'autopilot_changed_sources': autopilot_changed_sources_text,
            'enabling_autopilot_sources_allowed': helpers.enabling_autopilot_sources_allowed(ad_group_settings)
        })


class AdGroupAdsUpload(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_get')
    def get(self, request, ad_group_id):
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

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_post')
    def post(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        form = forms.AdGroupAdsUploadForm(request.POST, request.FILES)
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
            inserted_content_ads=0,
            propagated_content_ads=0,
            batch_size=len(content_ads),
        )
        batch.save()

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


class AdGroupAdsUploadReport(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_report_get')
    def get(self, request, ad_group_id, batch_id):
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


class AdGroupAdsUploadCancel(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_cancel_get')
    def get(self, request, ad_group_id, batch_id):
        helpers.get_ad_group(request.user, ad_group_id)

        try:
            batch = models.UploadBatch.objects.get(pk=batch_id)
        except models.UploadBatch.DoesNotExist():
            raise exc.MissingDataException()

        if batch.propagated_content_ads >= batch.batch_size:
            raise exc.ValidationError(errors={
                'cancel': 'Cancel action unsupported at this stage',
            })

        with transaction.atomic():
            batch.status = constants.UploadBatchStatus.CANCELLED
            batch.save(update_fields=['status'])

        return self.create_api_response()


class AdGroupAdsUploadStatus(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_upload_status_get')
    def get(self, request, ad_group_id, batch_id):
        helpers.get_ad_group(request.user, ad_group_id)

        try:
            batch = models.UploadBatch.objects.get(pk=batch_id)
        except models.UploadBatch.DoesNotExist():
            raise exc.MissingDataException()

        step = 1
        count = 0
        batch_size = batch.batch_size

        if batch.propagated_content_ads > 0:
            step = 4
            count = batch.propagated_content_ads
        elif batch.inserted_content_ads > 0:
            step = 3
            count = batch.inserted_content_ads
        else:
            step = 2
            count = batch.processed_content_ads

        response_data = {
            'status': batch.status,
            'count': count,
            'batch_size': batch_size,
            'step': step,
        }

        errors = self._get_error_details(batch, ad_group_id)
        if errors:
            response_data['errors'] = {
                'details': errors,
            }

        return self.create_api_response(response_data)

    def _get_error_details(self, batch, ad_group_id):
        errors = {}
        if batch.status == constants.UploadBatchStatus.FAILED:
            if batch.error_report_key:
                errors['report_url'] = reverse('ad_group_ads_upload_report',
                                               kwargs={'ad_group_id': ad_group_id, 'batch_id': batch.id})
                errors['description'] = 'Found {} error{}.'.format(
                    batch.num_errors, 's' if batch.num_errors > 1 else '')
            else:
                errors['description'] = 'An error occured while processing file.'
        elif batch.status == constants.UploadBatchStatus.CANCELLED:
            errors['description'] = 'Content Ads upload was cancelled.'

        return errors


class AdGroupContentAdArchive(api_common.BaseApiView):

    @influx.timer('dash.api')
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

        active_content_ads = content_ads.filter(state=constants.ContentAdSourceState.ACTIVE)
        if active_content_ads.exists():
            api.update_content_ads_state(active_content_ads, constants.ContentAdSourceState.INACTIVE, request)

        response = {
            'active_count': active_content_ads.count()
        }

        # reload
        content_ads = content_ads.all()

        api.update_content_ads_archived_state(request, content_ads, ad_group, archived=True)

        response['archived_count'] = content_ads.count()
        response['rows'] = {
            content_ad.id: {
                'archived': content_ad.archived,
                'status_setting': content_ad.state,
            }
            for content_ad in content_ads
        }

        return self.create_api_response(response)


class AdGroupContentAdRestore(api_common.BaseApiView):

    @influx.timer('dash.api')
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

        api.update_content_ads_archived_state(request, content_ads, ad_group, archived=False)

        return self.create_api_response({
            'rows': {content_ad.id: {
                'archived': content_ad.archived,
                'status_setting': content_ad.state,
            } for content_ad in content_ads}})


class AdGroupContentAdState(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'ad_group_content_ad_state_post')
    def post(self, request, ad_group_id):
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

        if content_ads.exists():
            api.update_content_ads_state(content_ads, state, request)
            api.add_content_ads_state_change_to_history_and_notify(ad_group, content_ads, state, request)

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

    @influx.timer('dash.api')
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
        include_archived = request.GET.get('archived') == 'true'

        content_ad_ids_selected = helpers.parse_get_request_content_ad_ids(request.GET, 'content_ad_ids_selected')
        content_ad_ids_not_selected = helpers.parse_get_request_content_ad_ids(
            request.GET, 'content_ad_ids_not_selected')

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

    @influx.timer('dash.api')
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
            self._handle_adgroup_blacklist(
                request,
                ad_group,
                level,
                state,
                publishers,
                publishers_selected,
                publishers_not_selected
            )

        if level == constants.PublisherBlacklistLevel.GLOBAL:
            self._handle_global_blacklist(
                request,
                ad_group,
                state,
                publishers,
                publishers_selected,
                publishers_not_selected
            )

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
        ignored_publishers = set(
            [
                (pub['domain'], ad_group.id, pub['source_id'], )
                for pub in publishers_not_selected
            ]
        )

        publisher_blacklist = self._create_adgroup_blacklist(
            ad_group,
            publishers + publishers_selected,
            state,
            level,
            ignored_publishers
        )

        # when blacklisting at campaign or account level we also need
        # to generate blacklist entries on external sources
        # for all adgroups in campaign or account
        related_publisher_blacklist = self._create_campaign_and_account_blacklist(
            ad_group, level, publishers + publishers_selected)

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
            self._write_adgroup_history(
                request,
                publisher_blacklist + related_publisher_blacklist,
                state,
                level
            )

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
        supported_ad_groups = []
        # filter all adgroups that do not have bidder media sources added
        # (they don't exist on bidder at all)
        for filtered_ad_group in filtered_ad_groups:
            supports_blacklist = False
            for source in filtered_ad_group.sources.all():
                if source.can_modify_publisher_blacklist_automatically():
                    supports_blacklist = True
                    break
            if supports_blacklist:
                supported_ad_groups.append(filtered_ad_group)
        filtered_ad_groups = supported_ad_groups

        ret = []
        source_cache = {}
        for publisher in publishers:
            domain = publisher['domain']
            if domain not in source_cache:
                source_cache[domain] = models.Source.objects.filter(id=publisher['source_id']).first()
            source = source_cache[domain]

            # don't generate publisher entries on adgroup and campaign level
            # for Outbrain since it only supports account level blacklisting
            if source.source_type.type == constants.SourceType.OUTBRAIN:
                continue

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

        # OB currently has a limit of 10 blocked publishers per marketer
        count_ob_blacklisted_publishers = models.PublisherBlacklist.objects.filter(
            account=ad_group.campaign.account,
            source__source_type__type=constants.SourceType.OUTBRAIN,
            status__in=(constants.PublisherStatus.BLACKLISTED, constants.PublisherStatus.PENDING)
        ).count()

        for publisher in publishers:
            domain = publisher['domain']
            if domain not in source_cache:
                source_cache[domain] = models.Source.objects.filter(id=publisher['source_id']).first()
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

            if level != constants.PublisherBlacklistLevel.ACCOUNT and\
                    source.source_type.type == constants.SourceType.OUTBRAIN:
                # only allow outbrain for account level
                continue

            if level == constants.PublisherBlacklistLevel.ACCOUNT and\
                    source.source_type.type == constants.SourceType.OUTBRAIN and\
                    count_ob_blacklisted_publishers >= constants.MAX_OUTBRAIN_BLACKLISTED_PUBLISHERS_PER_ACCOUNT:
                # don't request more than 10 publisher on Outbrain per
                # account to be attempted to be blacklisted
                # because actions will fail and manual cleanup will be
                # necessary
                logger.error('Attempted to blacklist more than 10 publishers per account on Outbrain')
                continue

            if level == constants.PublisherBlacklistLevel.ACCOUNT and\
                    source.source_type.type == constants.SourceType.OUTBRAIN and\
                    count_ob_blacklisted_publishers < constants.MAX_OUTBRAIN_BLACKLISTED_PUBLISHERS_PER_ACCOUNT:
                count_ob_blacklisted_publishers += 1

            # store blacklisted publishers and push to other sources
            existing_entry = models.PublisherBlacklist.objects.filter(
                name=publisher['domain'],
                source=source).filter(
                    publisher_helpers.create_queryset_by_key(ad_group, level)
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
                new_publ = models.PublisherBlacklist(
                    name=publisher['domain'],
                    source=source,
                    status=constants.PublisherStatus.PENDING
                )
                new_publ.fill_keys(ad_group, level)
                new_publ.save()

            external_id = publisher.get('external_id')
            adgroup_blacklist.add(
                (domain, ad_group.id, source, external_id)
            )
        if len(failed_publisher_mappings) > 0:
            logger.warning('Failed mapping {count} publisher source slugs {slug}'.format(
                count=count_failed_publisher,
                slug=','.join(failed_publisher_mappings))
            )

        kv_blacklist = [
            {
                'domain': dom,
                'ad_group_id': adgroup_id,
                'source': source_val,
                'external_id': ext_id,
            }
            for (dom, adgroup_id, source_val, ext_id,) in adgroup_blacklist
        ]

        return kv_blacklist

    def _handle_global_blacklist(self, request, ad_group, state, publishers, publishers_selected, publishers_not_selected):
        existing_blacklisted_publishers = models.PublisherBlacklist.objects.filter(
            everywhere=True
        ).values('name', 'source__id')

        existing_blacklisted_publishers = set(map(
            lambda pub: (pub['name'], pub['source__id'],),
            existing_blacklisted_publishers
        ))

        ignored_publishers = set(
            [(pub['domain'], pub['source_id']) for pub in publishers_not_selected]
        )

        global_blacklist = self._create_global_blacklist(
            ad_group,
            publishers + publishers_selected,
            state,
            existing_blacklisted_publishers.union(ignored_publishers),
            ignored_publishers
        )

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
            self._write_history(
                request,
                ad_group,
                state,
                global_blacklist,
                constants.PublisherBlacklistLevel.GLOBAL
            )

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

                if source.source_type.type == constants.SourceType.OUTBRAIN:
                    # Outbrain only has account level blacklist
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

        ret = [
            {
                'domain': pub.name,
                'source': pub.source
            }
            for pub in blacklist
        ]
        return ret

    def _write_adgroup_history(self, request, publishers, state, level):
        history_entries = {}
        for publisher in publishers:
            adgid = publisher['ad_group_id']
            history_entries[adgid] = history_entries.get(adgid, [])
            history_entries[adgid].append(publisher)

        for adgid, adg_publishers in history_entries.iteritems():
            ad_group = models.AdGroup.objects.get(pk=adgid)
            self._write_history(request, ad_group, state, adg_publishers, level)

    def _write_history(self, request, ad_group, state, blacklist, level):
        action_string = "Blacklisted" if state == constants.PublisherStatus.BLACKLISTED else "Enabled"

        level_description = ""
        if level == constants.PublisherBlacklistLevel.GLOBAL:
            level_description = 'globally'
        else:
            level_description = 'on {level} level'.format(
                level=constants.PublisherBlacklistLevel.get_text(level).lower()
            )

        pub_strings = [u"{pub} on {slug}".format(
                       pub=pub_bl['domain'],
                       slug=pub_bl['source'].name
                       ) for pub_bl in blacklist]
        pubs_string = u", ".join(pub_strings)

        changes_text = u'{action} the following publishers {level_description}: {pubs}.'.format(
            action=action_string,
            level_description=level_description,
            pubs=pubs_string
        )
        settings = ad_group.get_current_settings().copy_settings()
        settings.changes_text = changes_text
        settings.save(request)

        # at the moment we only have the publishers view on adgroup level
        # which means all blacklisting actions are stored in the settings
        # changes text of the current adgroup
        # TODO: revise this if making separate views per level
        helpers.log_useraction_if_necessary(
            request,
            publisher_helpers.get_useractiontype(level),
            ad_group=ad_group
        )

        email_helper.send_ad_group_notification_email(ad_group, request, changes_text)


class AllAccountsOverview(api_common.BaseApiView):

    @influx.timer('dash.api')
    @statsd_helper.statsd_timer('dash.api', 'all_accounts_overview')
    def get(self, request):
        if not request.user.has_perm('zemauth.can_access_all_accounts_infobox'):
            raise exc.AuthorizationError()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        header = {
            'title': None,
            'level': constants.InfoboxLevel.ALL_ACCOUNTS,
            'level_verbose': constants.InfoboxLevel.get_text(constants.InfoboxLevel.ALL_ACCOUNTS),
        }

        response = {
            'header': header,
            'basic_settings': self._basic_settings(start_date, end_date),
            'performance_settings': None
        }

        return self.create_api_response(response)

    def _basic_settings(self, start_date, end_date):
        settings = []

        count_active_accounts = infobox_helpers.count_active_accounts()
        settings.append(infobox_helpers.OverviewSetting(
            'Active accounts:',
            count_active_accounts,
            section_start=True,
            tooltip='Number of accounts with at least one campaign running'
        ))

        weekly_logged_users = infobox_helpers.count_weekly_logged_in_users()
        settings.append(infobox_helpers.OverviewSetting(
            'Logged-in users:',
            weekly_logged_users,
            tooltip="Number of users who logged-in in the past 7 days"
        ))

        weekly_active_users = infobox_helpers.get_weekly_active_users()
        weekly_active_user_emails = [u.email for u in weekly_active_users]
        email_list_setting = infobox_helpers.OverviewSetting(
            'Active users:',
            '{}'.format(len(weekly_active_users)),
            tooltip='Users who made self-managed actions in the past 7 days'
        )

        if weekly_active_user_emails != []:
            email_list_setting = email_list_setting.comment(
                'Show more',
                'Show less',
                '<br />'.join(weekly_active_user_emails),
            )
        settings.append(email_list_setting)

        weekly_sf_actions = infobox_helpers.count_weekly_selfmanaged_actions()
        settings.append(infobox_helpers.OverviewSetting(
            'Self-managed actions:',
            weekly_sf_actions,
            tooltip="Number of actions taken by self-managed users "
                    "in the past 7 days"
        ))

        yesterday_spend = infobox_helpers.get_yesterday_all_accounts_spend()
        settings.append(infobox_helpers.OverviewSetting(
            'Yesterday spend:',
            lc_helper.default_currency(yesterday_spend),
            tooltip='Yesterday media spend',
            section_start=True
        ))

        mtd_spend = infobox_helpers.get_mtd_all_accounts_spend()
        settings.append(infobox_helpers.OverviewSetting(
            'MTD spend:',
            lc_helper.default_currency(mtd_spend),
            tooltip='Month-to-date media spend',
        ))

        today = datetime.datetime.utcnow()
        start, end = calendar.monthrange(today.year, today.month)
        start_date = start_date or datetime.datetime(today.year, today.month, 1).date()
        end_date = end_date or datetime.datetime(today.year, today.month, end).date()

        total_budget = infobox_helpers.calculate_all_accounts_total_budget(
            start_date,
            end_date
        )
        settings.append(infobox_helpers.OverviewSetting(
            'Total budgets:',
            lc_helper.default_currency(total_budget),
            section_start=True,
            tooltip='Sum of total budgets in selected date range'
        ))

        monthly_budget = infobox_helpers.calculate_all_accounts_monthly_budget(today)
        settings.append(infobox_helpers.OverviewSetting(
            'Monthly budgets:',
            lc_helper.default_currency(monthly_budget),
            tooltip='Sum of total budgets for current month'
        ))

        return [setting.as_dict() for setting in settings]


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
        logger.debug('Sharethrough approval postback without signature. crid: %s', data['crid'])
    else:
        calculated = base64.urlsafe_b64encode(hmac.new(settings.SHARETHROUGH_PARAM_SIGN_KEY,
                                                       msg=str(data['crid']),
                                                       digestmod=hashlib.sha256)).digest()

        if sig != calculated:
            logger.debug('Invalid sharethrough signature. crid: %s', data['crid'])

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
