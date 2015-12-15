#!/usr/bin/python
# -*- coding: utf-8 -*-
from collections import OrderedDict
import json

from django.conf import settings
from django.db.models import Q

from dash.views import helpers
from dash import models
from dash import export_plus
from dash import constants
from dash import scheduled_report
from utils import api_common
from utils import statsd_helper
from utils import exc


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

        content = export_plus.get_csv_content(fieldnames, data)
        return self.create_csv_response(filename, content=content)


class ExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 500000
    MAX_DAYS = 366
    MAX_BREAKDOWN_DAYS = 32

    @statsd_helper.statsd_timer('dash.export_plus', 'export_plus_allowed_get')
    def get(self, request, level_, id_=None):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        num_days = (end_date - start_date).days + 1

        if level_ == 'ad_groups':
            ad_group = helpers.get_ad_group(user, id_)
            content_ad_rows = models.ContentAd.objects.filter(ad_group=ad_group).count()
            return self.create_api_response({
                'content_ad': content_ad_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'by_day': {
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS
                }
            })
        elif level_ == 'campaigns':
            campaign = helpers.get_campaign(user, id_)
            ad_groups = models.AdGroup.objects.filter(campaign=campaign).exclude_archived()
            ad_group_rows = ad_groups.count()
            content_ad_rows = models.ContentAd.objects.filter(ad_group=ad_groups).count()
            return self.create_api_response({
                'ad_group': ad_group_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'content_ad': content_ad_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'by_day': {
                    'ad_group': ad_group_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS
                }
            })
        elif level_ == 'accounts':
            account = helpers.get_account(user, id_)
            campaigns = models.Campaign.objects.filter(account=account).exclude_archived()
            ad_groups = models.AdGroup.objects.filter(campaign=campaigns).exclude_archived()
            campaign_rows = campaigns.count()
            ad_group_rows = ad_groups.count()
            content_ad_rows = models.ContentAd.objects.filter(ad_group=ad_groups).count()
            return self.create_api_response({
                'campaign': campaign_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'ad_group': ad_group_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'content_ad': content_ad_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'by_day': {
                    'ad_group': ad_group_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'campaign': campaign_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS
                }
            })
        elif level_ == 'all_accounts':
            accounts_num = models.Account.objects.all().filter_by_user(user).exclude_archived().count()
            campaigns_num = models.Campaign.objects.all().filter_by_user(user).exclude_archived().count()
            ad_groups_num = models.AdGroup.objects.all().filter_by_user(user).exclude_archived().count()
            return self.create_api_response({
                'account': accounts_num <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'campaign': campaigns_num <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'ad_group': ad_groups_num <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'by_day': {
                    'ad_group': ad_groups_num * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'campaign': campaigns_num * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'account': accounts_num * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS
                }
            })

        return self.create_api_response({
            'view': True
        })


class SourcesExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 500000
    MAX_DAYS = 366
    MAX_BREAKDOWN_DAYS = 32

    ALL_ACCOUNTS_BREAKDOWN_MANY_SOURCES = 3
    ALL_ACCOUNTS_MAX_BREAKDOWN_DAYS_WHEN_MANY_SOURCES = 15


    @statsd_helper.statsd_timer('dash.export_plus', 'sources_export_plus_allowed_get')
    def get(self, request, level_, id_=None):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user
        filtered_sources_num = len(helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources')))
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        num_days = (end_date - start_date).days + 1

        if level_ == 'ad_groups':
            ad_group = helpers.get_ad_group(user, id_)
            content_ad_rows = models.ContentAd.objects.filter(ad_group=ad_group).count() * filtered_sources_num
            return self.create_api_response({
                'ad_group': filtered_sources_num <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'content_ad': content_ad_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'by_day': {
                    'ad_group': filtered_sources_num * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS
                }
            })
        elif level_ == 'campaigns':
            campaign = helpers.get_campaign(user, id_)
            ad_groups = models.AdGroup.objects.filter(campaign=campaign)
            ad_group_rows = ad_groups.count() * filtered_sources_num
            content_ad_rows = models.ContentAd.objects.filter(ad_group__in=ad_groups).count() * filtered_sources_num
            return self.create_api_response({
                'campaign': filtered_sources_num <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'ad_group': ad_group_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'content_ad': content_ad_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'by_day': {
                    'ad_group': ad_group_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'campaign': filtered_sources_num * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS
                }
            })
        elif level_ == 'accounts':
            account = helpers.get_account(user, id_)
            campaigns = models.Campaign.objects.filter(account=account)
            ad_groups = models.AdGroup.objects.filter(campaign=campaigns)
            ad_group_rows = ad_groups.count() * filtered_sources_num
            campaign_rows = campaigns.count() * filtered_sources_num
            content_ad_rows = models.ContentAd.objects.filter(ad_group__in=ad_groups).count() * filtered_sources_num
            return self.create_api_response({
                'account': filtered_sources_num <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'campaign': campaign_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'ad_group': ad_group_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'content_ad': content_ad_rows <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'by_day': {
                    'ad_group': ad_group_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'content_ad': content_ad_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'campaign': campaign_rows * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'account': filtered_sources_num * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS
                }
            })
        elif level_ == 'all_accounts':
            accounts_num = models.Account.objects.all().filter_by_user(user).count()
            campaigns_num = models.Campaign.objects.all().filter_by_user(user).count()
            ad_groups_num = models.AdGroup.objects.all().filter_by_user(user).count()
            max_breakdown_days = (self.MAX_BREAKDOWN_DAYS if filtered_sources_num <= self.ALL_ACCOUNTS_BREAKDOWN_MANY_SOURCES else
                                  self.ALL_ACCOUNTS_MAX_BREAKDOWN_DAYS_WHEN_MANY_SOURCES)
            return self.create_api_response({
                'all_accounts': filtered_sources_num <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'account': accounts_num * filtered_sources_num <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'campaign': campaigns_num * filtered_sources_num <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'ad_group': ad_groups_num * filtered_sources_num <= self.MAX_ROWS and num_days <= self.MAX_DAYS,
                'by_day': {
                    'ad_group': num_days <= max_breakdown_days,
                    'campaign': num_days <= max_breakdown_days,
                    'account': accounts_num * filtered_sources_num * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS,
                    'all_accounts': filtered_sources_num * num_days <= self.MAX_ROWS and num_days <= self.MAX_BREAKDOWN_DAYS
                }
            })

        return self.create_api_response({})


class AccountCampaignsExport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'accounts_campaigns_export_plus_get')
    def get(self, request, account_id):
        content, filename = export_plus.get_report_from_request(request, account=helpers.get_account(request.user, account_id))
        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'accounts_campaigns_scheduled_report_put')
    def put(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        response = _add_scheduled_report_from_request(request, account=account)
        return self.create_api_response(response)


class CampaignAdGroupsExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'campaigns_ad_groups_export_plus_get')
    def get(self, request, campaign_id):
        content, filename = export_plus.get_report_from_request(request, campaign=helpers.get_campaign(request.user, campaign_id))
        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'campaigns_ad_groups_scheduled_report_put')
    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        response = _add_scheduled_report_from_request(request, campaign=campaign)
        return self.create_api_response(response)


class AdGroupAdsPlusExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'ad_group_ads_plus_export_plus_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        content, filename = export_plus.get_report_from_request(request, ad_group=ad_group)
        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_plus_scheduled_report_put')
    def put(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        response = _add_scheduled_report_from_request(request, ad_group=ad_group)
        return self.create_api_response(response)


class AllAccountsSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'all_accounts_sources_export_plus_get')
    def get(self, request):
        content, filename = export_plus.get_report_from_request(request, by_source=True)
        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'all_accounts_sources_scheduled_report_put')
    def put(self, request):
        response = _add_scheduled_report_from_request(request, by_source=True)
        return self.create_api_response(response)


class AccountSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'account_sources_export_plus_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        content, filename = export_plus.get_report_from_request(request, account=account, by_source=True)
        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'account_sources_scheduled_report_put')
    def put(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        response = _add_scheduled_report_from_request(request, account=account, by_source=True)
        return self.create_api_response(response)


class CampaignSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'campaign_sources_export_plus_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        content, filename = export_plus.get_report_from_request(request, campaign=campaign, by_source=True)
        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'campaign_sources_scheduled_report_put')
    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        response = _add_scheduled_report_from_request(request, campaign=campaign, by_source=True)
        return self.create_api_response(response)


class AdGroupSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'ad_group_sources_export_plus_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        content, filename = export_plus.get_report_from_request(request, ad_group=ad_group, by_source=True)
        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_scheduled_report_put')
    def put(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        response = _add_scheduled_report_from_request(request, ad_group=ad_group, by_source=True)
        return self.create_api_response(response)


class AllAccountsExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'all_accounts_export_plus_get')
    def get(self, request):
        content, filename = export_plus.get_report_from_request(request)
        return self.create_csv_response(filename, content=content)

    @statsd_helper.statsd_timer('dash.api', 'all_accounts_scheduled_report_put')
    def put(self, request):
        response = _add_scheduled_report_from_request(request)
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
        granularity=export_plus.get_granularity_from_type(r.get('type')),
        by_day=r.get('by_day') or False,
        by_source=by_source,
        ad_group=ad_group,
        campaign=campaign,
        account=account,
        sending_frequency=scheduled_report.get_sending_frequency(r.get('frequency')),
        recipient_emails=r.get('recipient_emails'))


class ScheduledReports(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'scheduled_reports_get')
    def get(self, request, account_id=None):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
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

        if not request.user.has_perm('zemauth.exports_plus') or scheduled_report.created_by != request.user:
            raise exc.ForbiddenError(message='Not allowed')

        scheduled_report.state = constants.ScheduledReportState.REMOVED
        scheduled_report.save()
        return self.create_api_response({})

    def format_reports(self, reports):
        result = []
        for r in reports:
            item = {}
            item['name'] = r.name

            item['level'] = ' - '.join(filter(None, [
                constants.ScheduledReportLevel.get_text(r.report.level),
                (r.report.account.name if r.report.account else ''),
                (r.report.campaign.account.name + ': ' + r.report.campaign.name if r.report.campaign else ''),
                (r.report.ad_group.campaign.account.name + ': '
                    + r.report.ad_group.campaign.name + ': '
                    + r.report.ad_group.name if r.report.ad_group else '')]))

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
