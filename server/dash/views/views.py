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
import hmac
import hashlib
import threading

from django.db import transaction
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt

import influx

from dash.views import helpers

from utils import lc_helper
from utils import api_common
from utils import exc
from utils import k1_helper
from utils import email_helper
from utils import request_signer

from automation import autopilot_plus

from automation import campaign_stop

from dash import models, region_targeting_helper, retargeting_helper
from dash import constants
from dash import api
from dash import forms
from dash import infobox_helpers
from dash import publisher_helpers
from dash import history_helpers
from dash import blacklist

import reports.api_publishers
import analytics.projections

logger = logging.getLogger(__name__)

YAHOO_DASH_URL = 'https://gemini.yahoo.com/advertiser/{advertiser_id}/campaign/{campaign_id}'
OUTBRAIN_DASH_URL = 'https://my.outbrain.com/amplify/site/marketers/{marketer_id}/reports/content?campaignId={campaign_id}'
FACEBOOK_DASH_URL = 'https://business.facebook.com/ads/manager/campaign/?ids={campaign_id}&business_id={business_id}'

# These agencies should have campaign stop turned off
# (for example Outbrain)
AGENCIES_WITHOUT_CAMPAIGN_STOP = {55}
ACCOUNTS_WITHOUT_CAMPAIGN_STOP = {490}


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


@login_required
def index(request):
    return render(request, 'index.html', {'staticUrl': settings.CLIENT_STATIC_URL, 'debug': settings.DEBUG})


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

    credentials = ad_group_source.source_credentials and ad_group_source.source_credentials.decrypt()
    if ad_group_source.source.source_type.type == constants.SourceType.YAHOO:
        url = YAHOO_DASH_URL.format(
            advertiser_id=json.loads(credentials)['advertiser_id'],
            campaign_id=ad_group_source.source_campaign_key
        )
    elif ad_group_source.source.source_type.type == constants.SourceType.OUTBRAIN:
        url = OUTBRAIN_DASH_URL.format(
            campaign_id=ad_group_source.source_campaign_key['campaign_id'],
            marketer_id=str(ad_group_source.source_campaign_key['marketer_id'])
        )
    elif ad_group_source.source.source_type.type == constants.SourceType.FACEBOOK:
        url = FACEBOOK_DASH_URL.format(
            campaign_id=ad_group_source.source_campaign_key,
            business_id=json.loads(credentials)['business_id'],
        )
    else:
        raise exc.MissingDataError()

    return render(request, 'redirect.html', {'url': url})


class User(api_common.BaseApiView):

    @influx.timer('dash.api')
    def get(self, request, user_id):
        response = {}

        if user_id == 'current':
            response['user'] = self.get_dict(request.user)

        return self.create_api_response(response)

    def get_dict(self, user):
        if not user:
            return {}

        agency = helpers.get_user_agency(user)
        return {
            'id': str(user.pk),
            'email': user.email,
            'name': user.get_full_name(),
            'agency': agency.id if agency else None,
            'permissions': user.get_all_permissions_with_access_levels(),
            'timezone_offset': pytz.timezone(settings.DEFAULT_TIME_ZONE).utcoffset(
                datetime.datetime.utcnow(), is_dst=True).total_seconds()
        }


class AccountArchive(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)
        account.archive(request)
        return self.create_api_response({})


class AccountRestore(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, account_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        account.restore(request)
        return self.create_api_response({})


class CampaignArchive(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.archive(request)
        return self.create_api_response({})


class CampaignRestore(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, campaign_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign.restore(request)

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
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        async_perf_query = AdGroupOverview.AsyncQuery(request.user, ad_group)
        async_perf_query.start()

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        ad_group_settings = ad_group.get_current_settings()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        ad_group_running_status = infobox_helpers.get_adgroup_running_status(ad_group_settings, filtered_sources)

        header = {
            'title': ad_group.name,
            'active': ad_group_running_status,
            'level': constants.InfoboxLevel.ADGROUP,
            'level_verbose': '{}: '.format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.ADGROUP)),
        }

        delivery = {
            'status': ad_group_running_status,
            'text': infobox_helpers.get_entity_delivery_text(ad_group_running_status)
        }

        basic_settings, daily_cap = self._basic_settings(request.user, ad_group, ad_group_settings)
        performance_settings = self._performance_settings(
            ad_group, request.user, ad_group_settings, start_date, end_date,
            daily_cap, async_perf_query
        )
        for setting in performance_settings[1:]:
            setting['section_start'] = True

        response = {
            'header': header,
            'delivery': delivery,
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

        if not user.has_perm('zemauth.can_see_new_infobox'):
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
                    ad_group_settings.tracking_code
                )
            settings.append(tracking_code_settings.as_dict())

        daily_cap = infobox_helpers.calculate_daily_ad_group_cap(ad_group)
        daily_cap_setting = infobox_helpers.OverviewSetting(
            'Daily Spend Cap:',
            lc_helper.default_currency(daily_cap) if daily_cap is not None else '',
            tooltip='Daily media spend cap'
        )
        settings.append(daily_cap_setting.as_dict())

        if not user.has_perm('zemauth.can_see_new_infobox'):
            if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
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
                        ', '.join(retargeted_adgroup_names)
                    )
                settings.append(retargetings_setting.as_dict())

        return settings, daily_cap

    def _performance_settings(self, ad_group, user, ad_group_settings, start_date, end_date,
                              daily_cap, async_query):
        settings = []

        async_query.join()
        yesterday_cost = async_query.yesterday_cost

        if not user.has_perm('zemauth.can_see_new_infobox'):
            monthly_proj = analytics.projections.CurrentMonthBudgetProjections(
                'campaign',
                campaign=ad_group.campaign
            )
            pacing = monthly_proj.total('pacing') or decimal.Decimal('0')

        if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            settings.append(infobox_helpers.create_yesterday_spend_setting(
                yesterday_cost,
                daily_cap
            ).as_dict())

            if not user.has_perm('zemauth.can_see_new_infobox'):
                settings.append(infobox_helpers.OverviewSetting(
                    'Campaign pacing:',
                    lc_helper.default_currency(monthly_proj.total('attributed_media_spend')),
                    description='{:.2f}% on plan'.format(pacing),
                    tooltip='Campaign pacing for the current month'
                ).as_dict())

        if user.has_perm('zemauth.campaign_goal_performance'):
            settings.extend(infobox_helpers.get_primary_campaign_goal(
                user,
                {'ad_group': ad_group},
                start_date,
                end_date
            ))

        return settings


class AdGroupArchive(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.archive(request)
        return self.create_api_response({})


class AdGroupRestore(api_common.BaseApiView):

    @influx.timer('dash.api')
    def post(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.archive_restore_entity'):
            raise exc.AuthorizationError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group.restore(request)

        for ad_group_source in ad_group.adgroupsource_set.all():
            api.refresh_publisher_blacklist(ad_group_source, request)
        return self.create_api_response({})


class CampaignAdGroups(api_common.BaseApiView):

    @influx.timer('dash.api')
    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        ad_group, ad_group_settings, changes_text = self._create_ad_group(campaign, request)
        ad_group_settings.save(None)

        api.update_ad_group_redirector_settings(ad_group, ad_group_settings)

        ad_group.write_history(
            changes_text,
            user=request.user,
            action_type=constants.HistoryActionType.CREATE)
        response = {
            'name': ad_group.name,
            'id': ad_group.id,
        }

        return self.create_api_response(response)

    def _create_ad_group(self, campaign, request):
        changes_text = None
        with transaction.atomic():
            ad_group = models.AdGroup(
                name=create_name(models.AdGroup.objects.filter(campaign=campaign), 'New ad group'),
                campaign=campaign
            )
            ad_group.save(request)
            ad_group_settings = self._create_new_settings(ad_group, request)
            if request.user.has_perm('zemauth.add_media_sources_automatically'):
                changes_text = self._add_media_sources(ad_group, ad_group_settings, request)

        k1_helper.update_ad_group(ad_group.pk,
                                  msg='CampaignAdGroups.put')

        return ad_group, ad_group_settings, changes_text

    def _create_new_settings(self, ad_group, request):
        current_settings = ad_group.get_current_settings()  # get default ad group settings
        new_settings = current_settings.copy_settings()
        campaign_settings = ad_group.campaign.get_current_settings()

        new_settings.target_devices = campaign_settings.target_devices
        new_settings.target_regions = campaign_settings.target_regions
        new_settings.ad_group_name = ad_group.name

        return new_settings

    def _add_media_sources(self, ad_group, ad_group_settings, request):
        sources = ad_group.campaign.account.allowed_sources.all()
        added_sources = []
        for source in sources:
            try:
                source_default_settings = helpers.get_source_default_settings(source)
            except exc.MissingDataError:
                logger.exception('Exception occurred on campaign with id %s', ad_group.campaign.pk)
                continue

            self._create_ad_group_source(request, source_default_settings, ad_group_settings)
            added_sources.append(source)

        changes_text = None
        if added_sources:
            changes_text = 'Created settings and automatically created campaigns for {} sources ({})'.format(
                len(added_sources), ', '.join([source.name for source in added_sources]))

        return changes_text

    def _create_ad_group_source(self, request, source_settings, ad_group_settings):
        ad_group = ad_group_settings.ad_group

        ad_group_source = helpers.add_source_to_ad_group(source_settings, ad_group)
        ad_group_source.save(None)
        helpers.set_ad_group_source_settings(
            None,
            ad_group_source,
            mobile_only=ad_group_settings.is_mobile_only()
        )
        return ad_group_source


class CampaignOverview(api_common.BaseApiView):

    @influx.timer('dash.api')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        campaign_settings = campaign.get_current_settings()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        campaign_running_status = infobox_helpers.get_campaign_running_status(campaign, campaign_settings)

        header = {
            'title': campaign.name,
            'active': campaign_running_status,
            'level': constants.InfoboxLevel.CAMPAIGN,
            'level_verbose': '{}: '.format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.CAMPAIGN)),
        }

        delivery = {
            'status': campaign_running_status,
            'text': infobox_helpers.get_entity_delivery_text(campaign_running_status)
        }

        basic_settings, daily_cap =\
            self._basic_settings(request.user, campaign, campaign_settings)

        performance_settings = self._performance_settings(
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
            'delivery': delivery,
            'basic_settings': basic_settings,
            'performance_settings': performance_settings,
        }
        return self.create_api_response(response)

    @influx.timer('dash.api')
    def _basic_settings(self, user, campaign, campaign_settings):
        settings = []

        if not user.has_perm('zemauth.can_see_new_infobox'):
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

        if not user.has_perm('zemauth.can_see_new_infobox'):
            post_click_tracking = []
            if campaign_settings.enable_ga_tracking:
                post_click_tracking.append('Google Analytics')
            if campaign_settings.enable_adobe_tracking:
                post_click_tracking.append('Adobe')

            if post_click_tracking == []:
                post_click_tracking.append("N/A")

            post_click_tracking_setting = infobox_helpers.OverviewSetting(
                'Post click tracking:',
                ', '.join(post_click_tracking),
            )
            settings.append(post_click_tracking_setting.as_dict())

            # take the num
            daily_cap = infobox_helpers.OverviewSetting(
                'Daily Spend Cap:',
                lc_helper.default_currency(daily_cap_value) if daily_cap_value > 0 else 'N/A',
                tooltip="Daily media spend cap",
                section_start=True
            )
            settings.append(daily_cap.as_dict())

        if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            campaign_budget_setting = infobox_helpers.create_total_campaign_budget_setting(user, campaign)
            settings.append(campaign_budget_setting.as_dict())

        return settings, daily_cap_value

    @influx.timer('dash.api')
    def _performance_settings(self, campaign, user, campaign_settings, daily_cap_cc,
                              start_date, end_date):
        settings = []

        monthly_proj = analytics.projections.CurrentMonthBudgetProjections(
            'campaign',
            campaign=campaign
        )

        pacing = monthly_proj.total('pacing') or decimal.Decimal('0')

        if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            yesterday_cost = infobox_helpers.get_yesterday_campaign_spend(user, campaign) or 0
            settings.append(infobox_helpers.create_yesterday_spend_setting(
                yesterday_cost,
                daily_cap_cc
            ).as_dict())

            settings.append(infobox_helpers.OverviewSetting(
                'Campaign pacing:',
                lc_helper.default_currency(monthly_proj.total('attributed_media_spend')),
                description='{:.2f}% on plan'.format(pacing),
                tooltip='Campaign pacing for the current month'
            ).as_dict())

        if user.has_perm('zemauth.campaign_goal_performance'):
            settings.extend(infobox_helpers.get_primary_campaign_goal(
                user,
                {'campaign': campaign},
                start_date,
                end_date
            ))

        return settings

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
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)

        account_running_status = infobox_helpers.get_account_running_status(account)

        header = {
            'title': account.name,
            'active': account_running_status,
            'level': constants.InfoboxLevel.ACCOUNT,
            'level_verbose': '{}: '.format(constants.InfoboxLevel.get_text(constants.InfoboxLevel.ACCOUNT)),
        }

        delivery = {
            'status': account_running_status,
            'text': infobox_helpers.get_entity_delivery_text(account_running_status)
        }

        basic_settings = self._basic_settings(request.user, account)

        performance_settings = self._performance_settings(account, request.user)
        for setting in performance_settings[1:]:
            setting['section_start'] = True

        response = {
            'header': header,
            'delivery': delivery,
            'basic_settings': basic_settings,
            'performance_settings': performance_settings,
        }

        return self.create_api_response(response)

    def _basic_settings(self, user, account):
        settings = []

        if not user.has_perm('zemauth.can_see_new_infobox'):
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

        sales_manager_setting_label = 'Sales Rep.:'
        if user.has_perm('zemauth.can_see_new_infobox'):
            sales_manager_setting_label = 'Sales Representative:'
        sales_manager_setting = infobox_helpers.OverviewSetting(
            sales_manager_setting_label,
            infobox_helpers.format_username(account_settings.default_sales_representative),
            tooltip='Sales Representative'
        )
        settings.append(sales_manager_setting.as_dict())

        if not user.has_perm('zemauth.can_see_new_infobox'):
            if user.has_perm('zemauth.can_see_account_type'):
                account_type_setting = infobox_helpers.OverviewSetting(
                    'Account Type:',
                    constants.AccountType.get_text(account_settings.account_type)
                )
                settings.append(account_type_setting.as_dict())

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

        if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            if not user.has_perm('zemauth.can_see_new_infobox'):
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
    def get(self, request):
        show_archived = request.GET.get('show_archived') == 'true'
        user_ad_groups = models.AdGroup.objects.all().filter_by_user(request.user)
        if not show_archived:
            user_ad_groups = user_ad_groups.exclude_archived()

        sources = []
        for source in models.Source.objects.filter(adgroupsource__ad_group__in=user_ad_groups).distinct():
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
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.ad_group_sources_add_source'):
            raise exc.MissingDataError()

        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        ad_group_settings = ad_group.get_current_settings()

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

        return self.create_api_response({
            'sources': sorted(sources, key=lambda source: source['name']),
            'sources_waiting': [],
        })

    @influx.timer('dash.api')
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
        ad_group_source.save(None)

        ad_group.write_history(
            '{} campaign created.'.format(ad_group_source.source.name),
            user=request.user,
            action_type=constants.HistoryActionType.MEDIA_SOURCE_ADD)
        helpers.set_ad_group_source_settings(
            None, ad_group_source,
            mobile_only=ad_group_settings.is_mobile_only(),
            max_cpc=ad_group_settings.cpc_cc
        )

        if settings.K1_CONSISTENCY_SYNC:
            api.add_content_ad_sources(ad_group_source)

        k1_helper.update_ad_group(ad_group_id, msg='AdGroupSources.put')
        return self.create_api_response(None)


class Account(api_common.BaseApiView):

    @influx.timer('dash.api')
    def put(self, request):
        if not request.user.has_perm('zemauth.all_accounts_accounts_add_account'):
            raise exc.MissingDataError()

        account = models.Account(name=create_name(models.Account.objects, 'New account'))

        managed_agency = models.Agency.objects.all().filter(
            users=request.user
        ).first()
        if managed_agency is not None:
            account.agency = managed_agency

        account.save(request)

        account.write_history(
            'Created account',
            user=request.user,
            action_type=constants.HistoryActionType.CREATE)

        settings = account.get_current_settings()
        settings.default_account_manager = request.user

        if managed_agency is not None:
            settings.default_sales_representative = managed_agency.sales_representative
            settings.account_type = constants.AccountType.ACTIVATED

        settings.save(request)

        response = {
            'name': account.name,
            'id': account.id
        }

        return self.create_api_response(response)


class AccountCampaigns(api_common.BaseApiView):

    @influx.timer('dash.api')
    def put(self, request, account_id):
        if not request.user.has_perm('zemauth.account_campaigns_view'):
            raise exc.MissingDataError()

        account = helpers.get_account(request.user, account_id)

        name = create_name(models.Campaign.objects.filter(account=account), 'New campaign')

        campaign = models.Campaign(
            name=name,
            account=account
        )
        campaign.save(request)

        settings = campaign.get_current_settings()  # creates new settings with default values
        settings.name = name
        settings.campaign_manager = request.user

        if account.id in ACCOUNTS_WITHOUT_CAMPAIGN_STOP or account.agency_id in AGENCIES_WITHOUT_CAMPAIGN_STOP:
            settings.automatic_campaign_stop = False

        settings.save(request, action_type=constants.HistoryActionType.CREATE)

        response = {
            'name': campaign.name,
            'id': campaign.id
        }

        return self.create_api_response(response)


class AdGroupSourceSettings(api_common.BaseApiView):

    @influx.timer('dash.api')
    def put(self, request, ad_group_id, source_id):
        resource = json.loads(request.body)
        ad_group = helpers.get_ad_group(request.user, ad_group_id, select_related=True)

        try:
            ad_group_source = models.AdGroupSource.objects.get(ad_group=ad_group, source_id=source_id)
        except models.AdGroupSource.DoesNotExist:
            raise exc.MissingDataError(message='Requested source not found')

        ad_group_source_settings = ad_group_source.get_current_settings()
        campaign_settings = ad_group.campaign.get_current_settings()

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

        ad_group_settings = ad_group.get_current_settings()
        source = models.Source.objects.get(pk=source_id)
        if 'state' in resource and state_form.cleaned_data.get('state') == constants.AdGroupSettingsState.ACTIVE:
            if not retargeting_helper.can_add_source_with_retargeting(source, ad_group_settings):
                errors.update(
                    {
                        'state': 'Cannot enable media source that does not support'
                        'retargeting on adgroup with retargeting enabled.'
                    }
                )
            elif not helpers.check_facebook_source(ad_group_source):
                errors.update(
                    {
                        'state': 'Cannot enable Facebook media source that isn\'t connected to a Facebook page.',
                    }
                )
            elif not helpers.check_yahoo_min_cpc(ad_group_settings, ad_group_source_settings):
                errors.update(
                    {
                        'state': 'Cannot enable Yahoo media source with the current settings - CPC too low',
                    }
                )

        if campaign_settings.landing_mode:
            for key in resource.keys():
                errors.update({key: 'Not allowed'})
        elif campaign_settings.automatic_campaign_stop:
            if 'daily_budget_cc' in resource:
                new_daily_budget = decimal.Decimal(resource['daily_budget_cc'])
                max_daily_budget = campaign_stop.get_max_settable_source_budget(
                    ad_group_source,
                    ad_group.campaign,
                    ad_group_source_settings,
                    ad_group_settings,
                    campaign_settings
                )
                if max_daily_budget is not None and new_daily_budget > max_daily_budget:
                    errors.update({
                        'daily_budget_cc': [
                            'Daily Spend Cap is too high. Maximum daily spend cap can be up to ${max_daily_budget}.'.format(
                                max_daily_budget=max_daily_budget
                            )
                        ]
                    })

            if 'state' in resource:
                can_enable_media_source = campaign_stop.can_enable_media_source(
                    ad_group_source, ad_group.campaign, campaign_settings, ad_group_settings)
                if not can_enable_media_source:
                    errors.update({
                        'state': ['Please add additional budget to your campaign to make changes.']
                    })

                if resource['state'] == constants.AdGroupSourceSettingsState.ACTIVE:
                    enabling_autopilot_sources_allowed = helpers.enabling_autopilot_sources_allowed(ad_group_settings)
                    if not enabling_autopilot_sources_allowed:
                        errors.update({
                            'state': ['Please increase Autopilot Daily Spend Cap to enable this source.']
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
                raise exc.ValidationError("Ad group end date in the past!")

        allowed_sources = {source.id for source in ad_group.campaign.account.allowed_sources.all()}

        api.set_ad_group_source_settings(ad_group_source, resource, request)
        autopilot_changed_sources_text = ''
        ad_group_settings = ad_group_source.ad_group.get_current_settings()
        if ad_group_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET and\
                'state' in resource:
            changed_sources = autopilot_plus.initialize_budget_autopilot_on_ad_group(ad_group, send_mail=False)
            autopilot_changed_sources_text = ', '.join([s.source.name for s in changed_sources])

        k1_helper.update_ad_group(ad_group.pk,
                                  msg='AdGroupSourceSettings.put')

        return self.create_api_response({
            'editable_fields': helpers.get_editable_fields(
                ad_group,
                ad_group_source,
                ad_group_settings,
                ad_group_source.get_current_settings_or_none(),
                campaign_settings,
                allowed_sources,
                campaign_stop.can_enable_media_source(ad_group_source, ad_group.campaign, campaign_settings, ad_group_settings)
            ),
            'autopilot_changed_sources': autopilot_changed_sources_text,
            'enabling_autopilot_sources_allowed': helpers.enabling_autopilot_sources_allowed(ad_group_settings)
        })


class PublishersBlacklistStatus(api_common.BaseApiView):

    @influx.timer('dash.api')
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

        self._handle_blacklisting(request, ad_group, level, state, publishers, publishers_selected,
                                  publishers_not_selected)

        response = {
            "success": True,
        }
        return self.create_api_response(response)

    def _handle_blacklisting(self, request, ad_group, level, state, publishers, publishers_selected,
                             publishers_not_selected):
        source_domains = self._generate_source_publishers(
            publishers, publishers_selected, publishers_not_selected
        )

        constraints = {}
        if level == constants.PublisherBlacklistLevel.ADGROUP:
            constraints['ad_group'] = ad_group
        elif level == constants.PublisherBlacklistLevel.CAMPAIGN:
            constraints['campaign'] = ad_group.campaign
        elif level == constants.PublisherBlacklistLevel.ACCOUNT:
            constraints['account'] = ad_group.campaign.account

        for source, domains in source_domains.iteritems():
            source_constraints = {'source': source}
            source_constraints.update(constraints)
            blacklist.update(ad_group, source_constraints, state, domains,
                             everywhere=level == constants.PublisherBlacklistLevel.GLOBAL)

        self._write_history(request, ad_group, state, [
            {'source': source, 'domain': d[0]}
            for source, domains in source_domains.iteritems()
            for d in domains
        ], level)

    def _generate_source_publishers(self, pubs, pubs_selected, pubs_ignored):
        source_publishers = {}
        source_ids = set()

        pubs_ignored_set = set(
            (publisher['source_id'], publisher['domain'])
            for publisher in pubs_ignored
        )

        for publisher in pubs + pubs_selected:
            source_id, domain = publisher['source_id'], publisher['domain']
            external_id = publisher.get('external_id')
            if (source_id, domain, ) in pubs_ignored_set:
                continue
            source_publishers.setdefault(source_id, set()).add((domain, external_id))
            source_ids.add(source_id)

        sources_map = {
            source.pk: source for source in models.Source.objects.filter(pk__in=source_ids)
        }

        return {
            sources_map[source_id]: domains
            for source_id, domains in source_publishers.iteritems()
        }

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

    def _write_history(self, request, ad_group, state, blacklist, level):
        action_string = "Blacklisted" if state == constants.PublisherStatus.BLACKLISTED \
                        else "Enabled"

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
        action_type = publisher_helpers.get_historyactiontype(level)
        entity = publisher_helpers.get_historyentity(ad_group, level)
        if entity is not None:
            entity.write_history(
                changes_text,
                user=request.user,
                action_type=action_type
            )
        else:
            history_helpers.write_global_history(
                changes_text,
                user=request.user,
                action_type=action_type
            )
        email_helper.send_ad_group_notification_email(ad_group, request, changes_text)


class AllAccountsOverview(api_common.BaseApiView):

    @influx.timer('dash.api')
    def get(self, request):
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        # infobox only filters by agency and account type
        view_filter = helpers.ViewFilter(request=request)

        header = {
            'title': None,
            'level': constants.InfoboxLevel.ALL_ACCOUNTS,
            'level_verbose': constants.InfoboxLevel.get_text(constants.InfoboxLevel.ALL_ACCOUNTS),
        }

        performance_settings = []
        if request.user.has_perm('zemauth.can_access_all_accounts_infobox'):
            basic_settings = self._basic_all_accounts_settings(request.user, start_date, end_date, view_filter)
            if request.user.has_perm('zemauth.can_see_new_infobox'):
                performance_settings = self._append_performance_all_accounts_settings(
                    performance_settings, request.user, view_filter
                )
                performance_settings = [setting.as_dict() for setting in performance_settings]
        elif request.user.has_perm('zemauth.can_access_agency_infobox'):
            basic_settings = self._basic_agency_settings(request.user, start_date, end_date, view_filter)
            if request.user.has_perm('zemauth.can_see_new_infobox'):
                performance_settings = self._append_performance_agency_settings(performance_settings, request.user)
                performance_settings = [setting.as_dict() for setting in performance_settings]
        else:
            raise exc.AuthorizationError()

        response = {
            'header': header,
            'basic_settings': basic_settings,
            'performance_settings': performance_settings if len(performance_settings) > 0 else None
        }

        return self.create_api_response(response)

    def _basic_agency_settings(self, user, start_date, end_date, view_filter):
        settings = []
        count_active_accounts = infobox_helpers.count_active_agency_accounts(user)
        settings.append(infobox_helpers.OverviewSetting(
            'Active accounts:',
            count_active_accounts,
            section_start=True,
            tooltip='Number of accounts with at least one campaign running'
        ))

        if not user.has_perm('zemauth.can_see_new_infobox'):
            settings = self._append_performance_agency_settings(settings, user)

        return [setting.as_dict() for setting in settings]

    def _basic_all_accounts_settings(self, user, start_date, end_date, view_filter):
        settings = []

        constraints = {}
        if view_filter.filtered_agencies:
            constraints['campaign__account__agency__in']\
                = view_filter.filtered_agencies
        if view_filter.filtered_account_types:
            latest_accset = models.AccountSettings.objects.all().group_current_settings()
            latest_typed_accset = models.AccountSettings.objects.all().filter(
                id__in=latest_accset
            ).filter(
                account_type__in=view_filter.filtered_account_types
            ).values_list('account__id', flat=True)
            constraints['campaign__account__id__in'] = latest_typed_accset

        count_active_accounts = infobox_helpers.count_active_accounts(
            view_filter.filtered_agencies,
            view_filter.filtered_account_types
        )
        settings.append(infobox_helpers.OverviewSetting(
            'Active accounts:',
            count_active_accounts,
            section_start=True,
            tooltip='Number of accounts with at least one campaign running'
        ))

        weekly_logged_users = infobox_helpers.count_weekly_logged_in_users(
            view_filter.filtered_agencies,
            view_filter.filtered_account_types
        )
        settings.append(infobox_helpers.OverviewSetting(
            'Logged-in users:',
            weekly_logged_users,
            tooltip="Number of users who logged-in in the past 7 days"
        ))

        weekly_active_users = infobox_helpers.get_weekly_active_users(
            view_filter.filtered_agencies,
            view_filter.filtered_account_types
        )
        weekly_active_user_emails = [u.email for u in weekly_active_users]
        email_list_setting = infobox_helpers.OverviewSetting(
            'Active users:',
            '{}'.format(len(weekly_active_users)),
            tooltip='Users who made self-managed actions in the past 7 days'
        )

        if weekly_active_user_emails != []:
            email_list_setting = email_list_setting.comment(
                'Show more',
                '<br />'.join(weekly_active_user_emails),
            )
        settings.append(email_list_setting)

        weekly_sf_actions = infobox_helpers.count_weekly_selfmanaged_actions(
            view_filter.filtered_agencies,
            view_filter.filtered_account_types
        )
        settings.append(infobox_helpers.OverviewSetting(
            'Self-managed actions:',
            weekly_sf_actions,
            tooltip="Number of actions taken by self-managed users "
                    "in the past 7 days"
        ))

        if not user.has_perm('zemauth.can_see_new_infobox'):
            settings = self._append_performance_all_accounts_settings(settings, user, view_filter)

        return [setting.as_dict() for setting in settings]

    def _append_performance_agency_settings(self, settings, user):
        if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            yesterday_spend = infobox_helpers.get_yesterday_agency_spend(user)
            settings.append(infobox_helpers.OverviewSetting(
                'Yesterday spend:',
                lc_helper.default_currency(yesterday_spend),
                tooltip='Yesterday media spend',
                section_start=True
            ))

            mtd_spend = infobox_helpers.get_mtd_agency_spend(user)
            mtd_spend_label = 'MTD spend:'
            if user.has_perm('zemauth.can_see_new_infobox'):
                mtd_spend_label = 'Month-to-date spend:'
            settings.append(infobox_helpers.OverviewSetting(
                mtd_spend_label,
                lc_helper.default_currency(mtd_spend),
                tooltip='Month-to-date media spend',
            ))

        return settings

    def _append_performance_all_accounts_settings(self, settings, user, view_filter):
        if user.has_perm('zemauth.can_view_platform_cost_breakdown'):
            yesterday_spend = infobox_helpers.get_yesterday_all_accounts_spend(
                view_filter.filtered_agencies,
                view_filter.filtered_account_types
            )
            settings.append(infobox_helpers.OverviewSetting(
                'Yesterday spend:',
                lc_helper.default_currency(yesterday_spend),
                tooltip='Yesterday media spend',
                section_start=True
            ))

            mtd_spend = infobox_helpers.get_mtd_all_accounts_spend(
                view_filter.filtered_agencies,
                view_filter.filtered_account_types
            )
            mtd_spend_label = 'MTD spend:'
            if user.has_perm('zemauth.can_see_new_infobox'):
                mtd_spend_label = 'Month-to-date spend:'
            settings.append(infobox_helpers.OverviewSetting(
                mtd_spend_label,
                lc_helper.default_currency(mtd_spend),
                tooltip='Month-to-date media spend',
            ))

        return settings


class Demo(api_common.BaseApiView):

    def get(self, request):
        if not request.user.has_perm('zemauth.can_request_demo_v3'):
            raise Http404('Forbidden')

        instance = self._start_instance()

        subject, body, _ = email_helper.format_email(constants.EmailTemplateType.DEMO_RUNNING, **instance)

        send_mail(
            subject,
            body,
            'Zemanta <{}>'.format(settings.FROM_EMAIL),
            [request.user.email],
            fail_silently=False
        )

        return self.create_api_response(instance)

    def _start_instance(self):
        request = urllib2.Request(settings.DK_DEMO_UP_ENDPOINT)
        response = request_signer.urllib2_secure_open(request, settings.DK_API_KEY)

        status_code = response.getcode()
        if status_code != 200:
            raise Exception('Invalid response status code. status code: {}'.format(status_code))

        ret = json.loads(response.read())
        if ret['status'] != 'success':
            raise Exception('Request not successful. status: {}'.format(ret['status']))

        return {
            'url': ret.get('instance_url'),
            'password': ret.get('instance_password'),
        }


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


class LiveStreamAllow(api_common.BaseApiView):

    def post(self, request):
        data = json.loads(request.body)
        email_helper.send_livestream_email(request.user, data['session_url'])
        return self.create_api_response({})
