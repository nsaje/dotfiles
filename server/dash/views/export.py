#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import logging

import influx

from django.db.models import Q
from django.conf import settings

from dash.views import helpers
from dash import models
from dash import export
from dash import constants
from dash import scheduled_report
from dash import history_helpers
from utils import api_common
from utils import exc
from utils import s3helpers

logger = logging.getLogger(__name__)


class ExportApiView(api_common.BaseApiView):

    def dispatch(self, request, *args, **kwargs):
        try:
            return super(api_common.BaseApiView, self).dispatch(request, *args, **kwargs)
        except Exception as e:
            return self.get_exception_response(request, e)


class ExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 500000
    ALL_ACC_BD_ADG_MAX_DAYS = 62
    ALL_ACC_BD_CAMP_MAX_DAYS = 160

    @influx.timer('dash.export_plus.allowed_get', type='default')
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
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        content, filename = export.get_report_from_request(request, account=account)

        account.write_history(
            'Exported report: {}'.format(filename),
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_csv_response(filename, content=content)

    def put(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        response = _add_scheduled_report_from_request(request, account=account)

        account.write_history(
            'Scheduled report.',
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_api_response(response)


class CampaignAdGroupsExport(ExportApiView):

    @influx.timer('dash.export_plus.campaign', type='ad_group')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        content, filename = export.get_report_from_request(request, campaign=campaign)

        campaign.write_history(
            'Exported report: {}'.format(filename),
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_csv_response(filename, content=content)

    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        response = _add_scheduled_report_from_request(request, campaign=campaign)

        campaign.write_history(
            'Scheduled report',
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_api_response(response)


class AdGroupAdsExport(ExportApiView):

    @influx.timer('dash.export_plus.ad_group', type='ads')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        content, filename = export.get_report_from_request(request, ad_group=ad_group)

        ad_group.write_history(
            'Exported report: {}'.format(filename),
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_csv_response(filename, content=content)

    def put(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        response = _add_scheduled_report_from_request(request, ad_group=ad_group)

        ad_group.write_history(
            'Scheduled report',
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_api_response(response)


class AllAccountsSourcesExport(ExportApiView):

    @influx.timer('dash.export_plus.all_accounts', type='sources')
    def get(self, request):
        content, filename = export.get_report_from_request(request, by_source=True)

        history_helpers.write_global_history(
            'Exported report: {}'.format(filename),
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_csv_response(filename, content=content)

    def put(self, request):
        response = _add_scheduled_report_from_request(request, by_source=True)

        history_helpers.write_global_history(
            'Scheduled report',
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_api_response(response)


class AccountSourcesExport(ExportApiView):

    @influx.timer('dash.export_plus.account', type='sources')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        content, filename = export.get_report_from_request(request, account=account, by_source=True)

        account.write_history(
            'Exported media sources report: {}'.format(filename),
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_csv_response(filename, content=content)

    def put(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        response = _add_scheduled_report_from_request(request, account=account, by_source=True)

        account.write_history(
            'Scheduled media sources report',
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_api_response(response)


class CampaignSourcesExport(ExportApiView):

    @influx.timer('dash.export_plus.campaign', type='sources')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        content, filename = export.get_report_from_request(request, campaign=campaign, by_source=True)

        campaign.write_history(
            'Exported media sources report: {}'.format(filename),
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_csv_response(filename, content=content)

    def put(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        response = _add_scheduled_report_from_request(request, campaign=campaign, by_source=True)

        campaign.write_history(
            'Scheduled media sources report',
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_api_response(response)


class AdGroupSourcesExport(ExportApiView):

    @influx.timer('dash.export_plus.ad_group', type='sources')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        content, filename = export.get_report_from_request(request, ad_group=ad_group, by_source=True)

        ad_group.write_history(
            'Exported media sources report: {}'.format(filename),
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_csv_response(filename, content=content)

    def put(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        response = _add_scheduled_report_from_request(request, ad_group=ad_group, by_source=True)

        ad_group.write_history(
            'Scheduled media sources report',
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_api_response(response)


class AllAccountsExport(ExportApiView):

    @influx.timer('dash.export_plus.all_accounts', type='default')
    def get(self, request):
        content, filename = export.get_report_from_request(request)

        history_helpers.write_global_history(
            'Exported report: {}'.format(filename),
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_csv_response(filename, content=content)

    def put(self, request):
        response = _add_scheduled_report_from_request(request)

        history_helpers.write_global_history(
            'Scheduled report',
            user=request.user,
            action_type=constants.HistoryActionType.REPORTING_MANAGE)

        return self.create_api_response(response)


def _add_scheduled_report_from_request(request, by_source=False, ad_group=None, campaign=None, account=None):
    try:
        r = json.loads(request.body)
    except ValueError:
        raise exc.ValidationError(message='Invalid json')
    filtered_sources = []
    filtered_agencies = None
    filtered_account_types = []
    if len(r.get('filtered_sources')) > 0:
        filtered_sources = helpers.get_filtered_sources(request.user, r.get('filtered_sources'))
    if ad_group is None and campaign is None and account is None:
        view_filter = helpers.ViewFilter(request)
        filtered_agencies = view_filter.filtered_agencies
        filtered_account_types = view_filter.filtered_account_types

    scheduled_report.add_scheduled_report(
        request.user,
        report_name=r.get('report_name'),
        filtered_sources=filtered_sources,
        filtered_agencies=filtered_agencies,
        filtered_account_types=filtered_account_types,
        order=r.get('order'),
        additional_fields=r.get('additional_fields'),
        granularity=export.get_granularity_from_type(r.get('type')),
        by_day=r.get('by_day') or False,
        by_source=by_source,
        include_model_ids=r.get('include_model_ids') or False,
        include_totals=r.get('include_totals') or False,
        ad_group=ad_group,
        campaign=campaign,
        account=account,
        sending_frequency=scheduled_report.get_sending_frequency(r.get('frequency')),
        day_of_week=r.get('day_of_week'),
        time_period=r.get('time_period'),
        recipient_emails=r.get('recipient_emails'))


class ScheduledReports(api_common.BaseApiView):

    def get(self, request, account_id=None):
        if account_id:
            account = helpers.get_account(request.user, account_id)
            reports = self.get_account_scheduled_reports(request.user, account)
        else:
            reports = self.get_all_accounts_scheduled_reports(request.user)
        response = {
            'reports': self.format_reports(reports, request.user)
        }
        return self.create_api_response(response)

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

        report = scheduled_report.report
        entity = report.ad_group or report.campaign or report.account
        if entity:
            entity.write_history(
                'Deleted scheduled report',
                action_type=constants.HistoryActionType.REPORTING_MANAGE
            )
        else:
            history_helpers.write_global_history(
                'Deleted scheduled report',
                action_type=constants.HistoryActionType.REPORTING_MANAGE
            )

    def format_reports(self, reports, user):
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
            if user.has_perm('zemauth.can_set_day_of_week_in_scheduled_reports'):
                item['day_of_week'] = constants.ScheduledReportDayOfWeek.get_text(r.day_of_week)
            if user.has_perm('zemauth.can_set_time_period_in_scheduled_reports'):
                item['time_period'] = constants.ScheduledReportTimePeriod.get_text(r.time_period)
            item['scheduled_report_id'] = r.id
            item['recipients'] = ', '.join(r.get_recipients_emails_list())
            result.append(item)
        return result

    def get_account_scheduled_reports(self, user, account):
        reports = models.ScheduledExportReport.objects.select_related('report').filter(
            ~Q(state=constants.ScheduledReportState.REMOVED),
            (Q(report__account=account) | Q(report__campaign__account=account) | Q(report__ad_group__campaign__account=account))
        )

        if account.get_current_settings().default_account_manager != user:
            reports = reports.filter(created_by=user)

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


class CustomReportDownload(ExportApiView):

    def get(self, request):
        if not request.user.has_perm('zemauth.can_download_custom_reports'):
            raise exc.AuthorizationError()
        path = request.GET.get('path')
        if not path:
            raise exc.ValidationError('Path not specified.')
        filename = path.split('/')[-1]
        s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
        try:
            content = s3.get(path)
        except:
            logger.exception('Failed to fetch {} from s3.'.format(path))
            raise exc.MissingDataError()
        return self.create_csv_response(filename, content=content)
