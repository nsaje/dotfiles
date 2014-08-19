import datetime
import json
import logging
import dateutil.parser
from collections import OrderedDict
import unicodecsv
from xlwt import Workbook, Style
import slugify
import excel_styles

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django.http import HttpResponse
import pytz

from utils import statsd_helper
from utils import api_common
from utils import exc
import actionlog.api
import actionlog.sync
import reports.api

from dash import forms
from dash import models
from dash import api

from zemauth.models import User as ZemUser

import constants

logger = logging.getLogger(__name__)

STATS_START_DELTA = 30
STATS_END_DELTA = 1


def get_ad_group(user, ad_group_id):
    try:
        return models.AdGroup.objects.get_for_user(user).\
            filter(id=int(ad_group_id)).get()
    except models.AdGroup.DoesNotExist:
        raise exc.MissingDataError('Ad Group does not exist')


def get_campaign(user, campaign_id):
    try:
        return models.Campaign.objects.get_for_user(user).\
            filter(id=int(campaign_id)).get()
    except models.Campaign.DoesNotExist:
        raise exc.MissingDataError('Campaign does not exist')


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
    data = reports.api.collect_results(data)

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
        result[c.ad_group_source.source_id] = c.get_latest_success()
    return result


def is_sync_recent(last_sync_datetime):
    min_sync_date = datetime.datetime.utcnow() - datetime.timedelta(
        hours=settings.ACTIONLOG_RECENT_HOURS
    )

    if not last_sync_datetime:
        return None

    result = last_sync_datetime >= pytz.utc.localize(min_sync_date)

    return result


@statsd_helper.statsd_timer('dash', 'index')
@login_required
def index(request):
    return render(request, 'index.html', {'staticUrl': settings.CLIENT_STATIC_URL})


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
                'permissions': list(user.get_all_permissions())
            }

        return result


class NavigationDataView(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'navigation_data_view_get')
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
                .filter(
                    Q(campaign__users__in=[user_id]) |
                    Q(campaign__groups__user__id=user_id) |
                    Q(campaign__account__users__in=[user_id]) |
                    Q(campaign__account__groups__user__id=user_id)
                )
            ).distinct('id')

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


class CampaignSettings(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaign_settings_get')
    def get(self, request, campaign_id):
        if not request.user.has_perm('dash.campaign_settings_view'):
            raise exc.MissingDataError()

        campaign = get_campaign(request.user, campaign_id)

        campaign_settings = self.get_current_settings(campaign)

        response = {
            'settings': self.get_dict(campaign_settings, campaign),
            'account_managers': self.get_user_list('campaign_settings_account_manager'),
            'sales_reps': self.get_user_list('campaign_settings_sales_rep'),
            'history': self.get_history(campaign)
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'ad_campaign_settings_put')
    def put(self, request, campaign_id):
        if not request.user.has_perm('dash.settings_view'):
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
        for i in range(0, len(settings) - 1):
            old_settings = settings[i]
            new_settings = settings[i + 1]

            changes = old_settings.get_setting_changes(new_settings)

            if not changes:
                continue

            settings_dict = self.convert_settings_to_dict(new_settings)

            history.append({
                'datetime': new_settings.created_dt,
                'changed_by': new_settings.created_by.email,
                'changes_text': self.convert_changes_to_string(changes, settings_dict),
                'settings': settings_dict.values()
            })

        return history

    def convert_settings_to_dict(self, settings):
        return OrderedDict([
            ('name', {
                'name': 'Name',
                'value': settings.name.encode('utf-8')
            }),
            ('account_manager', {
                'name': 'Account Manager',
                'value': settings.account_manager.get_full_name().encode('utf-8')
            }),
            ('service_representative', {
                'name': 'Sales Representative',
                'value': settings.sales_representative.get_full_name().encode('utf-8')
            }),
            ('service_fee', {
                'name': 'Service Fee',
                'value': constants.ServiceFee.get_text(settings.service_fee)
            }),
            ('iab_category', {
                'name': 'IAB Category',
                'value': constants.IABCategory.get_text(settings.iab_category)
            }),
            ('promotion_goal', {
                'name': 'Promotion Goal',
                'value': constants.PromotionGoal.get_text(settings.promotion_goal)
            })
        ])

    def convert_changes_to_string(self, changes, settings_dict):
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
                'service_fee': settings.service_fee,
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
        settings.service_fee = resource['service_fee']
        settings.iab_category = resource['iab_category']
        settings.promotion_goal = resource['promotion_goal']

    def get_user_list(self, perm_name):
        users = ZemUser.objects.get_users_with_perm(perm_name).order_by('last_name')
        return [{'id': str(user.id), 'name': user.get_full_name()} for user in users]


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

        ad_group = get_ad_group(request.user, ad_group_id)

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
        self.set_settings(settings, ad_group, form.cleaned_data)

        with transaction.atomic():
            ad_group.save()
            settings.save()

        api.order_ad_group_settings_update(ad_group, current_settings, settings)

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

    def set_settings(self, settings, ad_group, resource):
        settings.ad_group = ad_group
        settings.state = resource['state']
        settings.start_date = resource['start_date']
        settings.end_date = resource['end_date']
        settings.cpc_cc = resource['cpc_cc']
        settings.daily_budget_cc = resource['daily_budget_cc']
        settings.target_devices = resource['target_devices']
        settings.target_regions = resource['target_regions']
        settings.tracking_code = resource['tracking_code']


class AdGroupSourcesTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_table_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        sources_data = reports.api.query(
            get_stats_start_date(request.GET.get('start_date')),
            get_stats_end_date(request.GET.get('end_date')),
            ['source'],
            ad_group=int(ad_group.id)
        )
        sources_data = reports.api.collect_results(sources_data)

        sources = ad_group.sources.all().order_by('name')
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
        totals_data = reports.api.collect_results(totals_data)

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
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(ad_group),
        })

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
                'yesterday_cost': yesterday_cost.get(sid)
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
            for key in ['cost', 'cpc', 'ctr']:
                val = item[key]
                if not isinstance(val, float):
                    val = 0
                item[key] = '{:.2f}'.format(val)

            writer.writerow(item)

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


class AdGroupSync(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_sync')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        if not actionlog.api.is_sync_in_progress(ad_group):
            actionlog.sync.AdGroupSync(ad_group).trigger_all()

        return self.create_api_response({})


class AdGroupCheckSyncProgress(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_is_sync_in_progress')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        in_progress = actionlog.api.is_sync_in_progress(ad_group)

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

        rows = reports.api.collect_results(result_pg)

        totals_data = reports.api.query(start_date, end_date, ad_group=int(ad_group.id))
        totals_data = reports.api.collect_results(totals_data)

        last_sync = actionlog.sync.AdGroupSync(ad_group).get_latest_success()
        if last_sync:
            last_sync = pytz.utc.localize(last_sync)

        return self.create_api_response({
            'rows': rows,
            'totals': totals_data,
            'last_sync': last_sync,
            'is_sync_recent': is_sync_recent(last_sync),
            'is_sync_in_progress': actionlog.api.is_sync_in_progress(ad_group),
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
            totals_stats = reports.api.collect_results(totals_stats)

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
            breakdown_stats = reports.api.collect_results(breakdown_stats)

        return self.create_api_response({
            'stats': self.get_dict(breakdown_stats + totals_stats, sources)
        })

    def get_dict(self, stats, sources):
        sources_dict = {}
        if sources:
            sources_dict = {x.pk: x.name for x in sources}

        for stat in stats:
            if 'source' in stat:
                stat['source_name'] = sources_dict[stat['source']]

        return stats


@statsd_helper.statsd_timer('dash', 'healthcheck')
def healthcheck(request):
    return HttpResponse('OK')
