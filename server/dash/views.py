import datetime
import json
import logging

import dateutil.parser

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from actionlog import api as actionlog_api
from dash import api_common
from dash import exc
from dash import forms
from dash import models
from reports import api
from utils import statsd_helper

import constants

logger = logging.getLogger(__name__)

STATS_START_DELTA = 30
STATS_END_DELTA = 1


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
    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_get')
    def get(self, request, ad_group_id):
        try:
            ad_group = models.AdGroup.user_objects.get_for_user(request.user).\
                filter(id=int(ad_group_id)).get()
        except models.AdGroup.DoesNotExist:
            raise exc.MissingDataError('Ad Group does not exist')

        settings = self.get_current_settings(ad_group)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog_api.is_waiting(ad_group)
        }

        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_settings_put')
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

        if settings.state == constants.AdGroupSettingsState.INACTIVE and \
                settings.state != current_settings.state:
            actionlog_api.stop_ad_group(ad_group)

        response = {
            'settings': self.get_dict(settings, ad_group),
            'action_is_waiting': actionlog_api.is_waiting(ad_group)
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
        try:
            ad_group = models.AdGroup.user_objects.get_for_user(request.user).\
                filter(id=int(ad_group_id)).get()
        except models.AdGroup.DoesNotExist:
            raise exc.MissingDataError('Ad Group does not exist')

        networks_data = api.query(
            get_stats_start_date(request.GET.get('start_date')),
            get_stats_end_date(request.GET.get('end_date')),
            ['network'],
            ad_group=int(ad_group.id)
        )

        network_settings = models.AdGroupNetworkSettings.get_current_settings(ad_group)

        totals_data = api.query(
            get_stats_start_date(request.GET.get('start_date')),
            get_stats_end_date(request.GET.get('end_date')),
            ad_group=int(ad_group.id)
        )[0]

        return self.create_api_response({
            'rows': self.get_rows(ad_group, networks_data, network_settings),
            'totals': self.get_totals(ad_group, totals_data, network_settings)
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

    def get_rows(self, ad_group, networks_data, network_settings):
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

            rows.append({
                'name': settings.ad_group_network.network.name,
                'status': settings.state,
                'bid_cpc': float(settings.cpc_cc) if settings.cpc_cc is not None else None,
                'daily_budget': float(settings.daily_budget_cc) if settings.daily_budget_cc is not None else None,
                'cost': network_data.get('cost', None),
                'cpc': network_data.get('cpc', None),
                'clicks': network_data.get('clicks', None),
                'impressions': network_data.get('impressions', None),
                'ctr': network_data.get('ctr', None),
            })

        return rows


class AdGroupAdsTable(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_table_get')
    def get(self, request, ad_group_id):
        try:
            ad_group = models.AdGroup.user_objects.get_for_user(request.user).\
                filter(id=int(ad_group_id)).get()
        except models.AdGroup.DoesNotExist:
            raise exc.MissingDataError('Ad Group does not exist')

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

        article_data = api.query(
            start_date,
            end_date,
            ['article'],
            ad_group=int(ad_group.id),
            article=[article.id for article in articles]
        )

        totals_data = api.query(
            start_date,
            end_date,
            ad_group=int(ad_group.id)
        )[0]

        return self.create_api_response({
            'rows': self.get_rows(ad_group, article_data, articles),
            'totals': self.get_totals(totals_data),
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
        try:
            ad_group = models.AdGroup.user_objects.get_for_user(request.user).\
                filter(id=int(ad_group_id)).get()
        except models.AdGroup.DoesNotExist:
            raise exc.MissingDataError('Ad Group does not exist')

        stats = api.query(
            get_stats_start_date(request.GET.get('start_date')),
            get_stats_end_date(request.GET.get('end_date')),
            ['date'],
            ad_group=int(ad_group.id)
        )

        return self.create_api_response({
            'stats': stats
        })
