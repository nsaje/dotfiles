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
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
import pytz

from utils import statsd_helper
from utils import api_common
from utils import exc
import actionlog.api
import reports.api

from dash import forms
from dash import models
from dash import api

import constants

logger = logging.getLogger(__name__)

STATS_START_DELTA = 30
STATS_END_DELTA = 1


def get_ad_group(user, ad_group_id):
    try:
        return models.AdGroup.user_objects.get_for_user(user).\
            filter(id=int(ad_group_id)).get()
    except models.AdGroup.DoesNotExist:
        raise exc.MissingDataError('Ad Group does not exist')


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
    data = reports.api.query(
        start_date,
        end_date,
        dimensions,
        ad_group=int(ad_group_id)
    )

    if 'network' in dimensions:
        networks = {network.id: network for network in models.Network.objects.all()}
    if 'article' in dimensions:
        articles = {article.id: article for article in models.Article.objects.filter(ad_group=ad_group_id)}

    for item in data:
        if 'network' in dimensions:
            item['network'] = networks[item['network']].name
        if 'article' in dimensions:
            article = articles[item['article']]
            item['article'] = article.title
            item['url'] = article.url

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


def get_last_sucessful_sync_date(ad_group):
    networks_syncs = actionlog.api.get_last_succesfull_fetch_all_networks_dates(ad_group)
    if networks_syncs:
        last_sync = pytz.utc.localize(min(networks_syncs.values()))
    else:
        last_sync = None

    return last_sync


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
                'permissions': {
                    'actionlog_manual_view': user.has_perm('actionlog.manual_view'),
                }
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
                .filter(Q(campaign__users__in=[user_id]) | Q(campaign__account__users__in=[user_id]))
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


class AdGroupSettings(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        settings = self.get_current_settings(ad_group)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog.api.is_waiting_for_set_actions(ad_group)
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_put')
    def put(self, request, ad_group_id):
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


class AdGroupNetworksTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_networks_table_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        networks_data = reports.api.query(
            get_stats_start_date(request.GET.get('start_date')),
            get_stats_end_date(request.GET.get('end_date')),
            ['network'],
            ad_group=int(ad_group.id)
        )

        network_settings = models.AdGroupNetworkSettings.get_current_settings(ad_group)

        totals_data = reports.api.query(
            get_stats_start_date(request.GET.get('start_date')),
            get_stats_end_date(request.GET.get('end_date')),
            ad_group=int(ad_group.id)
        )[0]

        last_success_actions = \
            actionlog.api.get_last_succesfull_fetch_all_networks_dates(ad_group)

        last_sync = get_last_sucessful_sync_date(ad_group)

        return self.create_api_response({
            'rows': self.get_rows(
                ad_group,
                networks_data,
                network_settings,
                last_success_actions
            ),
            'totals': self.get_totals(ad_group, totals_data, network_settings),
            'last_sync': last_sync,
            'is_sync_recent': is_sync_recent(last_sync),
        })

    def get_totals(self, ad_group, totals_data, network_settings):
        return {
            'daily_budget': float(sum(settings.daily_budget_cc for settings in network_settings.values()
                                      if settings.daily_budget_cc is not None)),
            'cost': totals_data['cost'],
            'cpc': totals_data['cpc'],
            'clicks': totals_data['clicks'],
            'impressions': totals_data['impressions'],
            'ctr': totals_data['ctr'],
        }

    def get_rows(self, ad_group, networks_data, network_settings, last_actions):
        rows = []
        for nid in constants.AdNetwork.get_all():
            try:
                settings = network_settings[nid]
            except KeyError:
                logger.error(
                    'Missing ad group network settings for ad group %s and network %s' %
                    (ad_group.id, nid))
                continue

            # get network reports data
            network_data = {}
            for item in networks_data:
                if item['network'] == nid:
                    network_data = item
                    break

            last_sync = last_actions.get(nid)
            if last_sync:
                last_sync = pytz.utc.localize(last_sync)

            rows.append({
                'id': str(nid),
                'name': settings.ad_group_network.network.name,
                'status': settings.state,
                'bid_cpc': float(settings.cpc_cc) if settings.cpc_cc is not None else None,
                'daily_budget':
                    float(settings.daily_budget_cc)
                    if settings.daily_budget_cc is not None
                    else None,
                'cost': network_data.get('cost', None),
                'cpc': network_data.get('cpc', None),
                'clicks': network_data.get('clicks', None),
                'impressions': network_data.get('impressions', None),
                'ctr': network_data.get('ctr', None),
                'last_sync': last_sync
            })

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
            networks_results = generate_rows(
                ['date', 'network', 'article'],
                ad_group_id,
                start_date,
                end_date
            )

            return self.create_excel_response(ads_results, networks_results, filename)
        else:
            return self.create_csv_response(ads_results, filename)

    def create_csv_response(self, data, filename):
        response = self.create_file_response('text/csv; name="%s.csv"' % filename, '%s.csv' % filename)

        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('article', 'Title'),
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
            for key in ['cost', 'cpc', 'ctr']:
                val = item[key]
                if not isinstance(val, float):
                    val = 0
                item[key] = '{:.2f}'.format(val)

            writer.writerow(item)

        return response

    def create_excel_response(self, ads_data, networks_data, filename):
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
                (item['article'],),
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
            'Per Network Report',
            [(1, 6000), (2, 8000), (3, 4000), (7, 3000)],
            ['Date', 'Title', 'URL', 'Network', 'Cost', 'CPC', 'Clicks', 'Impressions', 'CTR'],
            networks_data,
            lambda item: [
                (item['date'], excel_styles.style_date),
                (item['article'],),
                (item['url'],),
                (item['network'],),
                (item['cost'] or 0, excel_styles.style_usd),
                (item['cpc'] or 0, excel_styles.style_usd),
                (item['clicks'] or 0,),
                (item['impressions'] or 0,),
                ((item['ctr'] or 0) / 100, excel_styles.style_percent)
            ]
        )

        workbook.save(response)
        return response


class AdGroupNetworksExport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_networks_export_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        start_date = get_stats_start_date(request.GET.get('start_date'))
        end_date = get_stats_end_date(request.GET.get('end_date'))

        filename = '{0}_{1}_per_networks_report_{2}_{3}'.format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.name),
            start_date,
            end_date
        )

        results = generate_rows(
            ['date', 'network'],
            ad_group.id,
            start_date,
            end_date
        )

        if request.GET.get('type') == 'excel':
            return self.create_excel_response(results, filename)
        else:
            return self.create_csv_response(results, filename)

    def create_csv_response(self, data, filename):
        response = self.create_file_response('text/csv; name="%s.csv"' % filename, '%s.csv' % filename)

        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('network', 'Network'),
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

    def create_excel_response(self, data, filename):
        response = self.create_file_response('application/octet-stream', '%s.xls' % filename)

        workbook = Workbook(encoding='UTF-8')

        create_excel_worksheet(
            workbook,
            'Per-Network Report',
            [(1, 6000), (5, 3000)],
            ['Date', 'Network', 'Cost', 'CPC', 'Clicks', 'Impressions', 'CTR'],
            data,
            lambda item: [
                (item['date'], excel_styles.style_date),
                (item['network'],),
                (item['cost'] or 0, excel_styles.style_usd),
                (item['cpc'] or 0, excel_styles.style_usd),
                (item['clicks'] or 0,),
                (item['impressions'] or 0,),
                ((item['ctr'] or 0) / 100, excel_styles.style_percent)
            ]
        )

        workbook.save(response)
        return response


class AdGroupAdsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_table_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        page = request.GET.get('page')
        size = request.GET.get('size')
        start_date = get_stats_start_date(request.GET.get('start_date'))
        end_date = get_stats_end_date(request.GET.get('end_date'))

        size = max(min(int(size or 5), 50), 1)

        article_list = models.Article.objects.filter(ad_group=ad_group).order_by('title')
        paginator = Paginator(article_list, size)

        try:
            articles = paginator.page(page)
        except PageNotAnInteger:
            articles = paginator.page(1)
        except EmptyPage:
            articles = paginator.page(paginator.num_pages)

        article_data = reports.api.query(
            start_date,
            end_date,
            ['article'],
            ad_group=int(ad_group.id),
            article=[article.id for article in articles]
        )

        totals_data = reports.api.query(
            start_date,
            end_date,
            ad_group=int(ad_group.id)
        )[0]

        last_sync = get_last_sucessful_sync_date(ad_group)

        return self.create_api_response({
            'rows': self.get_rows(ad_group, article_data, articles),
            'totals': self.get_totals(totals_data),
            'last_sync': last_sync,
            'is_sync_recent': is_sync_recent(last_sync),
            'pagination': {
                'currentPage': articles.number,
                'numPages': articles.paginator.num_pages,
                'count': articles.paginator.count,
                'startIndex': articles.start_index(),
                'endIndex': articles.end_index(),
                'size': size
            }
        })

    def get_totals(self, totals_data):
        return {
            'cost': totals_data['cost'],
            'cpc': totals_data['cpc'],
            'clicks': totals_data['clicks'],
            'impressions': totals_data['impressions'],
            'ctr': totals_data['ctr'],
        }

    def get_rows(self, ad_group, article_data, articles):
        rows = []
        for article in articles:
            data = {}
            for item in article_data:
                if item['article'] == article.id:
                    data = item
                    break

            rows.append({
                'id': str(article.pk),
                'url': article.url,
                'title': article.title,
                'cost': data.get('cost', None),
                'cpc': data.get('cpc', None),
                'clicks': data.get('clicks', None),
                'impressions': data.get('impressions', None),
                'ctr': data.get('ctr', None),
            })

        return rows


class AdGroupDailyStats(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_daily_stats_get')
    def get(self, request, ad_group_id):
        ad_group = get_ad_group(request.user, ad_group_id)

        article_ids = request.GET.getlist('article_ids')
        network_ids = request.GET.getlist('network_ids')
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
                ad_group=int(ad_group.id)
            )

        articles = None
        networks = None
        breakdown_stats = []
        extra_kwargs = {}

        if article_ids:
            ids = [int(x) for x in article_ids]
            extra_kwargs['article_id'] = ids
            breakdown.append('article')
            articles = models.Article.objects.filter(pk__in=ids)

        if network_ids:
            ids = [int(x) for x in network_ids]
            extra_kwargs['network_id'] = ids
            breakdown.append('network')
            networks = models.Network.objects.filter(pk__in=ids)

        if 'article' in breakdown or 'network' in breakdown:
            breakdown_stats = reports.api.query(
                get_stats_start_date(start_date),
                get_stats_end_date(end_date),
                breakdown,
                ad_group=int(ad_group.id),
                **extra_kwargs
            )

        return self.create_api_response({
            'stats': self.get_dict(breakdown_stats + totals_stats, articles, networks)
        })

    def get_dict(self, stats, articles, networks):
        articles_dict = {}
        if articles:
            articles_dict = {x.pk: x.title for x in articles}

        networks_dict = {}
        if networks:
            networks_dict = {x.pk: x.name for x in networks}

        for stat in stats:
            if 'article' in stat:
                stat['article_title'] = articles_dict[stat['article']]
            if 'network' in stat:
                stat['network_name'] = networks_dict[stat['network']]

        return stats


@statsd_helper.statsd_timer('dash', 'healthcheck')
def healthcheck(request):
    return HttpResponse('OK')
