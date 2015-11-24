#!/usr/bin/python
# -*- coding: utf-8 -*-

import slugify

from collections import OrderedDict

from django.conf import settings
from django.db.models import Q

from dash.views import helpers
from dash import models
from dash import export_plus
from dash import constants
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


class AccountCampaignsExport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'accounts_campaigns_export_plus_get')
    def get(self, request, account_id):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user
        account = helpers.get_account(user, account_id)

        filtered_sources = helpers.get_filtered_sources(user, request.GET.get('filtered_sources'))
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        export_type = request.GET.get('type')
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'

        if export_type == 'campaign-csv':
            filename = 'report'
            content = export_plus.AccountExport().get_data(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='campaign')
        elif export_type == 'adgroup-csv':
            filename = '-_by_ad_group_report'
            content = export_plus.AccountExport().get_data(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group')
        elif export_type == 'contentad-csv':
            filename = '-_by_content_ad_report'
            content = export_plus.AccountExport().get_data(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad')

        filename = '{0}_{1}_{2}_{3}'.format(
            slugify.slugify(account.name),
            filename,
            start_date,
            end_date
        )

        return self.create_csv_response(filename, content=content)


class CampaignAdGroupsExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'campaigns_ad_groups_export_plus_get')
    def get(self, request, campaign_id):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user
        campaign = helpers.get_campaign(user, campaign_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(user, request.GET.get('filtered_sources'))
        export_type = request.GET.get('type')
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'

        if export_type == 'adgroup-csv':
            filename = 'report'
            content = export_plus.CampaignExport().get_data(user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group')
        elif export_type == 'contentad-csv':
            filename = '-_by_content_ad_report'
            content = export_plus.CampaignExport().get_data(user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad')

        filename = '{0}_{1}_{2}_{3}_{4}'.format(
            slugify.slugify(campaign.account.name),
            slugify.slugify(campaign.name),
            filename,
            start_date,
            end_date
        )

        return self.create_csv_response(filename, content=content)


class ExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 200000

    @statsd_helper.statsd_timer('dash.export_plus', 'export_plus_allowed_get')
    def get(self, request, level_, id_=None):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user

        if level_ == 'ad_groups':
            ad_group = helpers.get_ad_group(user, id_)
            return self.create_api_response({
                'content_ad': models.ContentAd.objects.filter(ad_group=ad_group).count() <= self.MAX_ROWS
            })
        elif level_ == 'campaigns':
            campaign = helpers.get_campaign(user, id_)
            ad_groups = models.AdGroup.objects.filter(campaign=campaign).exclude_archived()
            return self.create_api_response({
                'ad_group': ad_groups.count() <= self.MAX_ROWS,
                'content_ad': models.ContentAd.objects.filter(ad_group=ad_groups).count() <= self.MAX_ROWS
            })
        elif level_ == 'accounts':
            account = helpers.get_account(user, id_)
            campaigns = models.Campaign.objects.filter(account=account).exclude_archived()
            ad_groups = models.AdGroup.objects.filter(campaign=campaigns).exclude_archived()
            return self.create_api_response({
                'campaign': campaigns.count() <= self.MAX_ROWS,
                'ad_group': ad_groups.count() <= self.MAX_ROWS,
                'content_ad': models.ContentAd.objects.filter(ad_group=ad_groups).count() <= self.MAX_ROWS
            })
        elif level_ == 'all_accounts':
            accounts_num = models.Account.objects.all().filter_by_user(user).exclude_archived().count()
            campaigns_num = models.Campaign.objects.all().filter_by_user(user).exclude_archived().count()
            ad_groups_num = models.AdGroup.objects.all().filter_by_user(user).exclude_archived().count()
            return self.create_api_response({
                'account': accounts_num <= self.MAX_ROWS,
                'campaign': campaigns_num <= self.MAX_ROWS,
                'ad_group': ad_groups_num <= self.MAX_ROWS
            })

        return self.create_api_response({
            'view': True
        })


class SourcesExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 200000

    @statsd_helper.statsd_timer('dash.export_plus', 'sources_export_plus_allowed_get')
    def get(self, request, level_, id_=None):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user
        filtered_sources_num = len(helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources')))
        if level_ == 'ad_groups':
            ad_group = helpers.get_ad_group(user, id_)
            return self.create_api_response({
                'ad_group': filtered_sources_num <= self.MAX_ROWS,
                'content_ad': models.ContentAd.objects.filter(ad_group=ad_group).count() * filtered_sources_num <= self.MAX_ROWS
            })
        elif level_ == 'campaigns':
            campaign = helpers.get_campaign(user, id_)
            ad_groups = models.AdGroup.objects.filter(campaign=campaign)
            return self.create_api_response({
                'campaign': filtered_sources_num <= self.MAX_ROWS,
                'ad_group': ad_groups.count() * filtered_sources_num <= self.MAX_ROWS,
                'content_ad': models.ContentAd.objects.filter(ad_group__in=ad_groups).count() * filtered_sources_num <= self.MAX_ROWS
            })
        elif level_ == 'accounts':
            account = helpers.get_account(user, id_)
            campaigns = models.Campaign.objects.filter(account=account)
            ad_groups = models.AdGroup.objects.filter(campaign=campaigns)
            return self.create_api_response({
                'account': filtered_sources_num <= self.MAX_ROWS,
                'campaign': campaigns.count() * filtered_sources_num <= self.MAX_ROWS,
                'ad_group': ad_groups.count() * filtered_sources_num <= self.MAX_ROWS,
                'content_ad': models.ContentAd.objects.filter(ad_group__in=ad_groups).count() * filtered_sources_num <= self.MAX_ROWS
            })
        elif level_ == 'all_accounts':
            accounts_num = models.Account.objects.all().filter_by_user(user).count()
            campaigns_num = models.Campaign.objects.all().filter_by_user(user).count()
            ad_groups_num = models.AdGroup.objects.all().filter_by_user(user).count()
            return self.create_api_response({
                'add_accounts': filtered_sources_num <= self.MAX_ROWS,
                'account': accounts_num * filtered_sources_num <= self.MAX_ROWS,
                'campaign': campaigns_num * filtered_sources_num <= self.MAX_ROWS,
                'ad_group': ad_groups_num * filtered_sources_num <= self.MAX_ROWS
            })

        return self.create_api_response({})


class AdGroupAdsPlusExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'ad_group_ads_plus_export_plus_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(user, request.GET.get('filtered_sources'))
        export_type = request.GET.get('type')
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'

        if export_type == 'contentad-csv':
            filename = '{0}_{1}_{2}_report_{3}_{4}'.format(
                slugify.slugify(ad_group.campaign.account.name),
                slugify.slugify(ad_group.campaign.name),
                slugify.slugify(ad_group.name),
                start_date,
                end_date
            )
            content = export_plus.AdGroupExport().get_data(user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad')
        return self.create_csv_response(filename, content=content)


class AllAccountsSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'all_accounts_sources_export_plus_get')
    def get(self, request):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(user, request.GET.get('filtered_sources'))
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'
        export_type = request.GET.get('type')

        if export_type == 'allaccounts-csv':
            filename = 'ZemantaOne_media_source_report'
            content = export_plus.AllAccountsExport().get_data(user, filtered_sources, start_date, end_date, order, additional_fields, by_source=True)
        elif export_type == 'account-csv':
            filename = 'ZemantaOne_-_by_account_media_source_report'
            content = export_plus.AllAccountsExport().get_data(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='account', by_source=True)
        elif export_type == 'campaign-csv':
            filename = 'ZemantaOne_-_by_campaign_media_source_report'
            content = export_plus.AllAccountsExport().get_data(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='campaign', by_source=True)
        elif export_type == 'adgroup-csv':
            filename = 'ZemantaOne_-_by_ad_group_media_source_report'
            content = export_plus.AllAccountsExport().get_data(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group', by_source=True)

        filename = '{0}_{1}_{2}'.format(
            filename,
            start_date,
            end_date
        )

        return self.create_csv_response(filename, content=content)


class AccountSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'account_sources_export_plus_get')
    def get(self, request, account_id):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user
        account = helpers.get_account(user, account_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(user, request.GET.get('filtered_sources'))
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'
        export_type = request.GET.get('type')

        if export_type == 'account-csv':
            filename = 'media_source_report'
            content = export_plus.AccountExport().get_data(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, by_source=True)
        elif export_type == 'campaign-csv':
            filename = '-_by_campaign_media_source_report'
            content = export_plus.AccountExport().get_data(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='campaign', by_source=True)
        elif export_type == 'adgroup-csv':
            filename = '-_by_ad_group_media_source_report'
            content = export_plus.AccountExport().get_data(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group', by_source=True)
        elif export_type == 'contentad-csv':
            filename = '-_by_content_ad_media_source_report'
            content = export_plus.AccountExport().get_data(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad', by_source=True)

        filename = '{0}_{1}_{2}_{3}'.format(
            slugify.slugify(account.name),
            filename,
            start_date,
            end_date
        )

        return self.create_csv_response(filename, content=content)


class CampaignSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'campaign_sources_export_plus_get')
    def get(self, request, campaign_id):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user
        campaign = helpers.get_campaign(user, campaign_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(user, request.GET.get('filtered_sources'))
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'
        export_type = request.GET.get('type')

        if export_type == 'campaign-csv':
            filename = 'media_source_report'
            content = export_plus.CampaignExport().get_data(user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='campaign', by_source=True)
        elif export_type == 'adgroup-csv':
            filename = '-_by_ad_group_media_source_report'
            content = export_plus.CampaignExport().get_data(user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group', by_source=True)
        elif export_type == 'contentad-csv':
            filename = '-_by_content_ad_media_source_report'
            content = export_plus.CampaignExport().get_data(user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad', by_source=True)

        filename = '{0}_{1}_{2}_{3}_{4}'.format(
            slugify.slugify(campaign.account.name),
            slugify.slugify(campaign.name),
            filename,
            start_date,
            end_date
        )

        return self.create_csv_response(filename, content=content)


class AdGroupSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'ad_group_sources_export_plus_get')
    def get(self, request, ad_group_id):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user
        ad_group = helpers.get_ad_group(user, ad_group_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(user, request.GET.get('filtered_sources'))
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'
        export_type = request.GET.get('type')

        if export_type == 'adgroup-csv':
            filename = 'media_source_report'
            content = export_plus.AdGroupExport().get_data(user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group', by_source=True)
        elif export_type == 'contentad-csv':
            filename = '-_by_content_ad_media_source_report'
            content = export_plus.AdGroupExport().get_data(user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad', by_source=True)

        filename = '{0}_{1}_{2}_{3}_{4}_{5}'.format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.campaign.name),
            slugify.slugify(ad_group.name),
            filename,
            start_date,
            end_date
        )

        return self.create_csv_response(filename, content=content)


class AllAccountsExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export_plus', 'all_accounts_export_plus_get')
    def get(self, request):
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        user = request.user

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(user, request.GET.get('filtered_sources'))
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'
        export_type = request.GET.get('type')

        if export_type == 'account-csv':
            filename = 'ZemantaOne_report'
            content = export_plus.AllAccountsExport().get_data(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='account')
        elif export_type == 'campaign-csv':
            filename = 'ZemantaOne_-_by_campaign_report'
            content = export_plus.AllAccountsExport().get_data(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='campaign')
        elif export_type == 'adgroup-csv':
            filename = 'ZemantaOne_-_by_ad_group_report'
            content = export_plus.AllAccountsExport().get_data(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group')

        filename = '{0}_{1}_{2}'.format(filename, start_date, end_date)

        return self.create_csv_response(filename, content=content)


class AccountReports(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_scheduled_reports_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        if not request.user.has_perm('zemauth.exports_plus'):
            raise exc.ForbiddenError(message='Not allowed')
        response = {
            'reports': self.format_reports(self.get_scheduled_reports(request.user, account))
        }
        return self.create_api_response(response)

    def format_reports(self, reports):
        result = []
        for r in reports:
            item = {}
            item['name'] = r.name
            item['level'] = ' - '.join(filter(None, [
                constants.ScheduledReportLevel.get_text(r.report.level),
                (r.report.campaign.name if r.report.campaign else ''),
                (r.report.ad_group.campaign.name + ': ' + r.report.ad_group.name if r.report.ad_group else '')]))
            item['granularity'] = ', '.join(filter(None, [
                constants.ScheduledReportGranularity.get_text(r.report.granularity),
                ('by Media Source' if r.report.breakdown_by_source else ''),
                ('by day' if r.report.breakdown_by_day else '')]))
            item['frequency'] = constants.ScheduledReportSendingFrequency.get_text(r.sending_frequency)
            item['scheduled_report_id'] = r.id
            item['recipients'] = ', '.join(r.get_recipients_emails_list())
            result.append(item)
        return result

    def get_scheduled_reports(self, user, account):
        reports = models.ScheduledExportReport.objects.select_related('report').filter(
            ~Q(state=constants.ScheduledReportState.REMOVED),
            Q(created_by=user),
            (Q(report__account=account) | Q(report__campaign__account=account) | Q(report__ad_group__campaign__account=account))
        )
        return reports


class AccountReportsRemove(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'account_scheduled_reports_get')
    def post(self, request, scheduled_report_id):
        scheduled_report = models.ScheduledExportReport.objects.get(id=scheduled_report_id)

        if not request.user.has_perm('zemauth.exports_plus') or scheduled_report.created_by != request.user:
            raise exc.ForbiddenError(message='Not allowed')

        scheduled_report.state = constants.ScheduledReportState.REMOVED
        scheduled_report.save()
        return self.create_api_response({})
