#!/usr/bin/python
# -*- coding: utf-8 -*-

from collections import OrderedDict
from functools import partial
import json

import influx

from django.conf import settings
from django.db.models import Q

from dash.views import helpers
from dash import models
from dash import export
from dash import constants
from dash import scheduled_report
from utils import api_common
from utils import statsd_helper
from utils import exc


log_direct_download_user_action = partial(helpers.log_useraction_if_necessary,
                                          user_action_type=constants.UserActionType.DOWNLOAD_REPORT)

log_schedule_report_user_action = partial(helpers.log_useraction_if_necessary,
                                          user_action_type=constants.UserActionType.SCHEDULE_REPORT)


class ExportApiView(api_common.BaseApiView):
    def dispatch(self, request, *args, **kwargs):
        try:
            return super(api_common.BaseApiView, self).dispatch(request, *args, **kwargs)
        except Exception as e:
            email = request.user.email
            if email == settings.DEMO_USER_EMAIL or email in settings.DEMO_USERS:
                return self._demo_export(request)
            return self.get_exception_response(request, e)

    def _demo_export(self, request):
        data = []
        filename = 'export'
        fieldnames = OrderedDict([
            ('date', 'Date'),
            ('cost', 'Cost'),
            ('cpc', 'Avg. CPC'),
            ('clicks', 'Clicks'),
            ('impressions', 'Impressions'),
            ('ctr', 'CTR')
        ])

        content = export.get_csv_content(fieldnames, data)
        return self.create_csv_response(filename, content=content)


class ExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 500000
    ALL_ACC_BD_ADG_MAX_DAYS = 62
    ALL_ACC_BD_CAMP_MAX_DAYS = 160

    @influx.timer('dash.export_plus.allowed_get', type='default')
    @statsd_helper.statsd_timer('dash.export_plus', 'export_plus_allowed_get')
    def get(self, request, level_, id_=None):
        user = request.user
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        num_days = (end_date - start_date).days + 1

        if level_ == 'ad_groups':
            ad_group = helpers.get_ad_group(user, id_)
            content_ad_rows = models.ContentAd.objects.filter(ad_group=ad_group).count()
            return self.create_api_response({
                'ad_group': True,
                'content_ad': content_ad_rows <= self.MAX_ROWS,
                'by_day': {
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS
                }
            })
        elif level_ == 'campaigns':
            campaign = helpers.get_campaign(user, id_)
            ad_groups = models.AdGroup.objects.filter(campaign=campaign).exclude_archived()
            ad_group_rows = ad_groups.count()
            content_ad_rows = models.ContentAd.objects.filter(ad_group__in=ad_groups).count()
            return self.create_api_response({
                'campaign': True,
                'ad_group': ad_group_rows <= self.MAX_ROWS,
                'content_ad': content_ad_rows <= self.MAX_ROWS,
                'by_day': {
                    'ad_group': ad_group_rows * num_days <= self.MAX_ROWS,
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS
                }
            })
        elif level_ == 'accounts':
            account = helpers.get_account(user, id_)
            campaigns = models.Campaign.objects.filter(account=account).exclude_archived()
            ad_groups = models.AdGroup.objects.filter(campaign__in=campaigns).exclude_archived()
            campaign_rows = campaigns.count()
            ad_group_rows = ad_groups.count()
            content_ad_rows = models.ContentAd.objects.filter(ad_group__in=ad_groups).count()
            return self.create_api_response({
                'account': True,
                'campaign': campaign_rows <= self.MAX_ROWS,
                'ad_group': ad_group_rows <= self.MAX_ROWS,
                'content_ad': content_ad_rows <= self.MAX_ROWS,
                'by_day': {
                    'ad_group': ad_group_rows * num_days <= self.MAX_ROWS,
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS,
                    'campaign': campaign_rows * num_days <= self.MAX_ROWS
                }
            })
        elif level_ == 'all_accounts':
            accounts_num = models.Account.objects.all().filter_by_user(user).exclude_archived().count()
            campaigns_num = models.Campaign.objects.all().filter_by_user(user).exclude_archived().count()
            ad_groups_num = models.AdGroup.objects.all().filter_by_user(user).exclude_archived().count()
            return self.create_api_response({
                'all_accounts': True,
                'account': accounts_num <= self.MAX_ROWS,
                'campaign': campaigns_num <= self.MAX_ROWS,
                'ad_group': ad_groups_num <= self.MAX_ROWS,
                'by_day': {
                    'ad_group': num_days <= self.ALL_ACC_BD_ADG_MAX_DAYS,
                    'campaign': num_days <= self.ALL_ACC_BD_CAMP_MAX_DAYS,
                    'account': accounts_num * num_days <= self.MAX_ROWS
                }
            })
        return self.create_api_response({
            'view': True
        })


class SourcesExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 500000
    ALL_ACC_BD_ADG_MAX_DAYS = 11
    ALL_ACC_BD_CAMP_MAX_DAYS = 21
    ALL_ACC_BD_ACC_MAX_DAYS = 62

    @influx.timer('dash.export_plus.allowed_get', type='sources')
    @statsd_helper.statsd_timer('dash.export_plus', 'sources_export_plus_allowed_get')
    def get(self, request, level_, id_=None):
        user = request.user
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        num_days = (end_date - start_date).days + 1

        if level_ == 'ad_groups':
            ad_group = helpers.get_ad_group(user, id_)
            active_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
            num_sources = len(set([a.source for a in active_sources]).intersection(filtered_sources))
            content_ad_rows = models.ContentAd.objects.filter(ad_group=ad_group).count() * num_sources
            return self.create_api_response({
                'ad_group': num_sources <= self.MAX_ROWS,
                'content_ad': content_ad_rows <= self.MAX_ROWS,
                'by_day': {
                    'ad_group': num_sources * num_days <= self.MAX_ROWS,
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS
                }
            })
        elif level_ == 'campaigns':
            campaign = helpers.get_campaign(user, id_)
            active_sources = helpers.get_active_ad_group_sources(models.Campaign, [campaign])
            num_sources = len(set([a.source for a in active_sources]).intersection(filtered_sources))
            ad_groups = models.AdGroup.objects.filter(campaign=campaign)
            ad_group_rows = ad_groups.count() * num_sources
            content_ad_rows = models.ContentAd.objects.filter(ad_group__in=ad_groups).count() * num_sources
            return self.create_api_response({
                'campaign': num_sources <= self.MAX_ROWS,
                'ad_group': ad_group_rows <= self.MAX_ROWS,
                'content_ad': content_ad_rows <= self.MAX_ROWS,
                'by_day': {
                    'ad_group': ad_group_rows * num_days <= self.MAX_ROWS,
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS,
                    'campaign': num_sources * num_days <= self.MAX_ROWS
                }
            })
        elif level_ == 'accounts':
            account = helpers.get_account(user, id_)
            active_sources = helpers.get_active_ad_group_sources(models.Account, [account])
            num_sources = len(set([a.source for a in active_sources]).intersection(filtered_sources))
            campaigns = models.Campaign.objects.filter(account=account)
            ad_groups = models.AdGroup.objects.filter(campaign__in=campaigns)
            ad_group_rows = ad_groups.count() * num_sources
            campaign_rows = campaigns.count() * num_sources
            content_ad_rows = models.ContentAd.objects.filter(ad_group__in=ad_groups).count() * num_sources
            return self.create_api_response({
                'account': num_sources <= self.MAX_ROWS,
                'campaign': campaign_rows <= self.MAX_ROWS,
                'ad_group': ad_group_rows <= self.MAX_ROWS,
                'content_ad': content_ad_rows <= self.MAX_ROWS,
                'by_day': {
                    'ad_group': ad_group_rows * num_days <= self.MAX_ROWS,
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS,
                    'campaign': campaign_rows * num_days <= self.MAX_ROWS,
                    'account': num_sources * num_days <= self.MAX_ROWS
                }
            })
        elif level_ == 'all_accounts':
            all_accounts = models.Account.objects.all().filter_by_user(user)
            active_sources = helpers.get_active_ad_group_sources(models.Account, all_accounts)
            num_sources = len(set([a.source for a in active_sources]).intersection(filtered_sources))
            accounts_num = len(all_accounts)
            campaigns_num = models.Campaign.objects.all().filter_by_user(user).count()
            ad_groups_num = models.AdGroup.objects.all().filter_by_user(user).count()
            many_sources = num_sources > 3
            return self.create_api_response({
                'all_accounts': num_sources <= self.MAX_ROWS,
                'account': accounts_num * num_sources <= self.MAX_ROWS,
                'campaign': campaigns_num * num_sources <= self.MAX_ROWS,
                'ad_group': ad_groups_num * num_sources <= self.MAX_ROWS,
                'by_day': {
                    'ad_group': num_days <= (self.ALL_ACC_BD_ADG_MAX_DAYS if many_sources else self.ALL_ACC_BD_ADG_MAX_DAYS * 3),
                    'campaign': num_days <= (self.ALL_ACC_BD_CAMP_MAX_DAYS if many_sources else self.ALL_ACC_BD_CAMP_MAX_DAYS * 3),
                    'account': num_days <= (self.ALL_ACC_BD_ACC_MAX_DAYS if many_sources else self.ALL_ACC_BD_ACC_MAX_DAYS * 3),
                    'all_accounts': num_sources * num_days <= self.MAX_ROWS
                }
            })
        return self.create_api_response({
            'view': True
        })


class AccountCampaignsExport(api_common.BaseApiView):
    @influx.timer('dash.export_plus.account', type='campaigns')
    @statsd_helper.statsd_timer('dash.export_plus', 'accounts_campaigns_export_plus_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        content, filename = export.get_report_from_request(request, account=account)

        log_direct_download_user_action(request, account=account)

        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'accounts_campaigns_scheduled_report_put')
    def put(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        response = _add_scheduled_report_from_request(request, account=account)

        log_schedule_report_user_action(request, account=account)

        return self.create_api_response(response)


class CampaignAdGroupsExport(ExportApiView):
    @influx.timer('dash.export_plus.campaign', type='ad_group')
    @statsd_helper.statsd_timer('dash.export_plus', 'campaigns_ad_groups_export_plus_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        content, filename = export.get_report_from_request(request, campaign=campaign)

        log_direct_download_user_action(request, campaign=campaign)

        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'campaigns_ad_groups_scheduled_report_put')
    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        response = _add_scheduled_report_from_request(request, campaign=campaign)

        log_schedule_report_user_action(request, campaign=campaign)

        return self.create_api_response(response)


class AdGroupAdsExport(ExportApiView):
    @influx.timer('dash.export_plus.ad_group', type='ads')
    @statsd_helper.statsd_timer('dash.export_plus', 'ad_group_ads_plus_export_plus_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        content, filename = export.get_report_from_request(request, ad_group=ad_group)

        log_direct_download_user_action(request, ad_group=ad_group)

        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_scheduled_report_put')
    def put(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        response = _add_scheduled_report_from_request(request, ad_group=ad_group)

        log_schedule_report_user_action(request, ad_group=ad_group)

        return self.create_api_response(response)


class AllAccountsSourcesExport(ExportApiView):
    @influx.timer('dash.export_plus.all_accounts', type='sources')
    @statsd_helper.statsd_timer('dash.export_plus', 'all_accounts_sources_export_plus_get')
    def get(self, request):
        content, filename = export.get_report_from_request(request, by_source=True)

        log_direct_download_user_action(request)

        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'all_accounts_sources_scheduled_report_put')
    def put(self, request):
        response = _add_scheduled_report_from_request(request, by_source=True)

        log_schedule_report_user_action(request)

        return self.create_api_response(response)


class AccountSourcesExport(ExportApiView):
    @influx.timer('dash.export_plus.account', type='sources')
    @statsd_helper.statsd_timer('dash.export_plus', 'account_sources_export_plus_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        content, filename = export.get_report_from_request(request, account=account, by_source=True)

        log_direct_download_user_action(request, account=account)

        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'account_sources_scheduled_report_put')
    def put(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        response = _add_scheduled_report_from_request(request, account=account, by_source=True)

        log_schedule_report_user_action(request, account=account)

        return self.create_api_response(response)


class CampaignSourcesExport(ExportApiView):
    @influx.timer('dash.export_plus.campaign', type='sources')
    @statsd_helper.statsd_timer('dash.export_plus', 'campaign_sources_export_plus_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        content, filename = export.get_report_from_request(request, campaign=campaign, by_source=True)

        log_direct_download_user_action(request, campaign=campaign)

        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'campaign_sources_scheduled_report_put')
    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        response = _add_scheduled_report_from_request(request, campaign=campaign, by_source=True)

        log_schedule_report_user_action(request, campaign=campaign)

        return self.create_api_response(response)


class AdGroupSourcesExport(ExportApiView):
    @influx.timer('dash.export_plus.ad_group', type='sources')
    @statsd_helper.statsd_timer('dash.export_plus', 'ad_group_sources_export_plus_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        content, filename = export.get_report_from_request(request, ad_group=ad_group, by_source=True)

        log_direct_download_user_action(request, ad_group=ad_group)

        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_scheduled_report_put')
    def put(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        response = _add_scheduled_report_from_request(request, ad_group=ad_group, by_source=True)

        log_schedule_report_user_action(request, ad_group=ad_group)

        return self.create_api_response(response)


class AllAccountsExport(ExportApiView):
    @influx.timer('dash.export_plus.all_accounts', type='default')
    @statsd_helper.statsd_timer('dash.export_plus', 'all_accounts_export_plus_get')
    def get(self, request):
        content, filename = export.get_report_from_request(request)

        log_direct_download_user_action(request)

        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'all_accounts_scheduled_report_put')
    def put(self, request):
        response = _add_scheduled_report_from_request(request)

        log_schedule_report_user_action(request)

        return self.create_api_response(response)


def _add_scheduled_report_from_request(request, by_source=False, ad_group=None, campaign=None, account=None):
    try:
        r = json.loads(request.body)
    except ValueError:
        raise exc.ValidationError(message='Invalid json')
    filtered_sources = []
    if len(r.get('filtered_sources')) > 0:
        filtered_sources = helpers.get_filtered_sources(request.user, r.get('filtered_sources'))
    scheduled_report.add_scheduled_report(
        request.user,
        report_name=r.get('report_name'),
        filtered_sources=filtered_sources,
        order=r.get('order'),
        additional_fields=r.get('additional_fields'),
        granularity=export.get_granularity_from_type(r.get('type')),
        by_day=r.get('by_day') or False,
        by_source=by_source,
        include_model_ids=r.get('include_model_ids') or False,
        ad_group=ad_group,
        campaign=campaign,
        account=account,
        sending_frequency=scheduled_report.get_sending_frequency(r.get('frequency')),
        recipient_emails=r.get('recipient_emails'))


class ScheduledReports(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'scheduled_reports_get')
    def get(self, request, account_id=None):
        if account_id:
            account = helpers.get_account(request.user, account_id)
            reports = self.get_account_scheduled_reports(request.user, account)
        else:
            reports = self.get_all_accounts_scheduled_reports(request.user)
        response = {
            'reports': self.format_reports(reports)
        }
        return self.create_api_response(response)

    @statsd_helper.statsd_timer('dash.api', 'scheduled_reports_delete')
    def delete(self, request, scheduled_report_id):
        scheduled_report = models.ScheduledExportReport.objects.get(id=scheduled_report_id)

        if scheduled_report.created_by != request.user:
            raise exc.ForbiddenError(message='Not allowed')

        scheduled_report.state = constants.ScheduledReportState.REMOVED
        scheduled_report.save()

        self._log_deletion_user_action(request, scheduled_report)

        return self.create_api_response({})

    def _log_deletion_user_action(self, request, scheduled_report):
        log_data = {}
        if scheduled_report.report:
            log_data = {
                'ad_group': scheduled_report.report.ad_group,
                'campaign': scheduled_report.report.campaign,
                'account': scheduled_report.report.account,
            }

        helpers.log_useraction_if_necessary(request, constants.UserActionType.DELETE_SCHEDULED_REPORT, **log_data)

    def format_reports(self, reports):
        result = []
        for r in reports:
            item = {}
            item['name'] = r.name

            item['level'] = ' - '.join(filter(None, [
                constants.ScheduledReportLevel.get_text(r.report.level),
                (r.report.account.name if r.report.account else ''),
                (r.report.campaign.account.name + ': ' + r.report.campaign.name if r.report.campaign else ''),
                (r.report.ad_group.campaign.account.name + ': ' +
                    r.report.ad_group.campaign.name + ': ' +
                    r.report.ad_group.name if r.report.ad_group else '')]))

            item['granularity'] = ', '.join(filter(None, [
                constants.ScheduledReportGranularity.get_text(r.report.granularity),
                ('by Media Source' if r.report.breakdown_by_source else ''),
                ('by day' if r.report.breakdown_by_day else '')]))

            item['frequency'] = constants.ScheduledReportSendingFrequency.get_text(r.sending_frequency)
            item['scheduled_report_id'] = r.id
            item['recipients'] = ', '.join(r.get_recipients_emails_list())
            result.append(item)
        return result

    def get_account_scheduled_reports(self, user, account):
        reports = models.ScheduledExportReport.objects.select_related('report').filter(
            ~Q(state=constants.ScheduledReportState.REMOVED),
            Q(created_by=user),
            (Q(report__account=account) | Q(report__campaign__account=account) | Q(report__ad_group__campaign__account=account))
        )
        return reports

    def get_all_accounts_scheduled_reports(self, user):
        reports = models.ScheduledExportReport.objects.select_related('report').filter(
            ~Q(state=constants.ScheduledReportState.REMOVED),
            Q(created_by=user)
        )
        return reports


class AdGroupAdsExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 16134

    @influx.timer('dash.export')
    @statsd_helper.statsd_timer('dash.export', 'ad_group_ads_export_allowed_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        num_days = (end_date - start_date).days + 1

        num_articles = models.Article.objects.filter(ad_group=ad_group).count()

        active_sources = helpers.get_active_ad_group_sources(models.AdGroup, [ad_group])
        num_sources = models.Source.objects.filter(
            adgroupsource__in=active_sources
        ).count()

        # estimate number of rows (worst case)
        row_count = num_days * num_sources * num_articles

        try:
            max_days = self.MAX_ROWS / (num_articles * num_sources)
        except ZeroDivisionError:
            max_days = None

        return self.create_api_response({
            'allowed': row_count <= self.MAX_ROWS,
            'max_days': max_days
        })


class CampaignAdGroupsExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 8072

    @influx.timer('dash.export')
    @statsd_helper.statsd_timer('dash.export', 'campiagn_ad_group_export_allowed_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        num_days = (end_date - start_date).days + 1

        num_articles = models.Article.objects.filter(ad_group__campaign=campaign).count()

        # estimate number of rows (worst case)
        row_count = num_days * num_articles

        try:
            max_days = self.MAX_ROWS / num_articles
        except ZeroDivisionError:
            max_days = None

        return self.create_api_response({
            'allowed': row_count <= self.MAX_ROWS,
            'max_days': max_days
        })
