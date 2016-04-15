#!/usr/bin/python
# -*- coding: utf-8 -*-

import slugify

from collections import OrderedDict

import influx

from django.conf import settings

from dash.views import helpers
from dash import models
from dash import export
from dash import constants
from utils import api_common
from utils import statsd_helper
from utils.sort_helper import sort_results
from utils import exc

from reports.api_helpers import POSTCLICK_ACQUISITION_FIELDS, POSTCLICK_ENGAGEMENT_FIELDS


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
        if request.GET.get('type') == 'excel':
            detailed_data = []
            columns = [
                {'key': 'date', 'name': 'Date', 'format': 'date'},
                {'key': 'cost', 'name': 'Cost', 'format': 'currency'},
                {'key': 'cpc', 'name': 'Avg. CPC', 'format': 'currency'},
                {'key': 'clicks', 'name': 'Clicks'},
                {'key': 'impressions', 'name': 'Impressions', 'width': 15},
                {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
            ]

            detailed_columns = list(columns)  # make a copy
            detailed_columns.insert(1, {'key': 'campaign', 'name': 'Campaign', 'width': 30})

            content = export.get_excel_content([
                ('Per Account Report', columns, data),
                ('Detailed Report', detailed_columns, detailed_data)
            ])

            return self.create_excel_response(filename, content=content)
        else:
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


class AccountCampaignsExport(api_common.BaseApiView):
    @influx.timer('dash.export')
    @statsd_helper.statsd_timer('dash.export', 'accounts_campaigns_export_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)

        campaigns = models.Campaign.objects.all().filter_by_user(request.user).filter(account=account)

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filename = '{0}_per_account_report_{1}_{2}'.format(
            slugify.slugify(account.name),
            start_date,
            end_date
        )

        data = export.generate_rows(
            ['date'],
            start_date,
            end_date,
            request.user,
            campaign=campaigns,
            source=filtered_sources,
        )

        if request.GET.get('type') == 'excel':
            detailed_data = export.generate_rows(
                ['date', 'campaign'],
                start_date,
                end_date,
                request.user,
                campaign=campaigns,
                source=filtered_sources,
            )

            self.add_campaign_data(detailed_data, campaigns)

            columns = [
                {'key': 'date', 'name': 'Date', 'format': 'date'},
                {'key': 'cost', 'name': 'Cost', 'format': 'currency'},
                {'key': 'cpc', 'name': 'Avg. CPC', 'format': 'currency'},
                {'key': 'clicks', 'name': 'Clicks'},
                {'key': 'impressions', 'name': 'Impressions', 'width': 15},
                {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
            ]

            detailed_columns = list(columns)  # make a copy
            detailed_columns.insert(1, {'key': 'campaign', 'name': 'Campaign', 'width': 30})

            content = export.get_excel_content([
                ('Per Account Report', columns, data),
                ('Detailed Report', detailed_columns, detailed_data)
            ])

            return self.create_excel_response(filename, content=content)
        else:
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

    def add_campaign_data(self, results, campaigns):
        campaign_names = {campaign.id: campaign.name for campaign in campaigns}

        for result in results:
            result['campaign'] = campaign_names[result['campaign']]


class CampaignAdGroupsExport(ExportApiView):
    @influx.timer('dash.export')
    @statsd_helper.statsd_timer('dash.export', 'campaigns_ad_groups_export_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        conversion_goals = []
        if request.user.has_perm('zemauth.conversion_reports'):
            conversion_goals = campaign.conversiongoal_set.all()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        export_type = request.GET.get('type')

        if export_type == 'excel_detailed' and \
                not request.user.has_perm('zemauth.campaign_ad_groups_detailed_report'):
            raise exc.MissingDataError()

        filename_format = '{0}_{1}_per_campaign_report_{2}_{3}'

        data = export.generate_rows(
            ['date'],
            start_date,
            end_date,
            request.user,
            conversion_goals=conversion_goals,
            campaign=campaign,
            source=filtered_sources,
        )

        if export_type == 'excel' or export_type == 'excel_detailed':
            detailed_data = export.generate_rows(
                ['date', 'ad_group'],
                start_date,
                end_date,
                request.user,
                conversion_goals=conversion_goals,
                campaign=campaign,
                source=filtered_sources,
            )

            self.add_ad_group_data(detailed_data, campaign)
            detailed_data = sort_results(detailed_data, ['date', 'ad_group'])

            # define columns
            columns = [
                {'key': 'date', 'name': 'Date', 'format': 'date'},
                {'key': 'cost', 'name': 'Cost', 'format': 'currency'},
                {'key': 'cpc', 'name': 'Avg. CPC', 'format': 'currency'},
                {'key': 'clicks', 'name': 'Clicks'},
                {'key': 'impressions', 'name': 'Impressions', 'width': 15},
                {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
            ]

            for conversion_goal in conversion_goals:
                columns.append({'key': conversion_goal.get_view_key(conversion_goals), 'name': conversion_goal.name})

            detailed_columns = list(columns)  # make a copy
            detailed_columns.insert(1, {'key': 'ad_group', 'name': 'Ad Group', 'width': 30})

            sheets = [
                ('Per Campaign Report', columns, data),
                ('Detailed Report', detailed_columns, detailed_data)
            ]

            if export_type == 'excel_detailed':
                filename_format = '{0}_{1}_per_campaign_detailed_report_{2}_{3}'
                breakdown = ['date', 'ad_group']

                if campaign.account.id == 53:
                    # temp for FindTheBest account, will be removed
                    # when we switch to content ad stats for all accounts
                    breakdown.append('content_ad')
                else:
                    breakdown.append('article')

                per_content_ad_data = export.generate_rows(
                    breakdown,
                    start_date,
                    end_date,
                    request.user,
                    conversion_goals=conversion_goals,
                    campaign=campaign
                )

                self.add_ad_group_data(per_content_ad_data, campaign)
                per_content_ad_data = sort_results(per_content_ad_data, ['date', 'ad_group', 'title'])

                per_content_ad_columns = list(detailed_columns)
                per_content_ad_columns.insert(2, {'key': 'title', 'name': 'Title', 'width': 30})
                per_content_ad_columns.insert(3, {'key': 'url', 'name': 'URL', 'width': 40})

                sheets.append(('Per Content Ad Report', per_content_ad_columns, per_content_ad_data))

            content = export.get_excel_content(sheets)

            return self.create_excel_response(filename_format.format(
                slugify.slugify(campaign.account.name),
                slugify.slugify(campaign.name),
                start_date,
                end_date
            ), content=content)
        else:
            fieldnames = OrderedDict([
                ('date', 'Date'),
                ('cost', 'Cost'),
                ('cpc', 'Avg. CPC'),
                ('clicks', 'Clicks'),
                ('impressions', 'Impressions'),
                ('ctr', 'CTR')
            ])

            for conversion_goal in conversion_goals:
                fieldnames[conversion_goal.get_view_key(conversion_goals)] = conversion_goal.name

            content = export.get_csv_content(fieldnames, data)
            return self.create_csv_response(filename_format.format(
                slugify.slugify(campaign.account.name),
                slugify.slugify(campaign.name),
                start_date,
                end_date
            ), content=content)

    def add_ad_group_data(self, results, campaign):
        ad_groups = {ad_group.id: ad_group for ad_group in models.AdGroup.objects.filter(campaign=campaign)}

        for result in results:
            result['ad_group'] = ad_groups[result['ad_group']].name


class AdGroupAdsPlusExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 16134

    @influx.timer('dash.export')
    @statsd_helper.statsd_timer('dash.export', 'ad_group_ads_plus_export_allowed_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        num_days = (end_date - start_date).days + 1

        num_contnent_ad_sources = models.ContentAdSource.objects.filter(ad_group=ad_group).count()

        # estimate number of rows (worst case)
        row_count = num_days * num_contnent_ad_sources

        try:
            max_days = self.MAX_ROWS / (num_contnent_ad_sources)
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


class AdGroupAdsPlusExport(ExportApiView):

    common_csv_columns = [
        ('image_url', 'Image URL'),
        ('title', 'Title'),
        ('url', 'URL'),
        ('uploaded', 'Uploaded'),
        ('cost', 'Spend'),
        ('cpc', 'Avg. CPC'),
        ('clicks', 'Clicks'),
        ('impressions', 'Impressions'),
        ('ctr', 'CTR'),
        ('visits', 'Visits'),
        ('click_discrepancy', 'Click Discrepancy'),
        ('pageviews', 'Pageviews'),
        ('percent_new_users', '% New Users'),
        ('bounce_rate', 'Bounce Rate'),
        ('pv_per_visit', 'PV/Visit'),
        ('avg_tos', 'Avg. ToS')
    ]

    # this duplication might look strange but is necessary - excel package does
    # runtime magic substitution of percent format with it's internal types
    common_csv_columns_w_date = [
        ('date', 'Date'),
    ] + common_csv_columns

    common_excel_columns = [
        {'key': 'image_url', 'name': 'Image URL', 'width': 40},
        {'key': 'title', 'name': 'Title', 'width': 30},
        {'key': 'url', 'name': 'URL', 'width': 40},
        {'key': 'uploaded', 'name': 'Uploaded', 'width': 40, 'format': 'date'},
        {'key': 'cost', 'name': 'Spend', 'width': 40},
        {'key': 'cpc', 'name': 'Avg. CPC', 'format': 'currency'},
        {'key': 'clicks', 'name': 'Clicks'},
        {'key': 'impressions', 'name': 'Impressions', 'width': 15},
        {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
        {'key': 'visits', 'name': 'Visits'},
        {'key': 'click_discrepancy', 'name': 'Click Discrepancy', 'format': 'percent'},
        {'key': 'pageviews', 'name': 'Pageviews'},
        {'key': 'percent_new_users', 'name': '% New Users', 'format': 'percent'},
        {'key': 'bounce_rate', 'name': 'Bounce Rate', 'format': 'percent'},
        {'key': 'pv_per_visit', 'name': 'PV/Visit', 'format': 'decimal'},
        {'key': 'avg_tos', 'name': 'Avg. ToS', 'format': 'decimal'}
    ]

    # this duplication might look strange but is necessary - excel package does
    # runtime magic substitution of percent format with it's internal types
    common_excel_columns_w_date = [
        {'key': 'date', 'name': 'Date', 'format': 'date'},
    ] + common_excel_columns

    @influx.timer('dash.export')
    @statsd_helper.statsd_timer('dash.export', 'ad_group_ads_plus_export_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        conversion_goals = []
        if request.user.has_perm('zemauth.conversion_reports'):
            conversion_goals = ad_group.campaign.conversiongoal_set.all()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        filename = '{0}_{1}_detailed_report_{2}_{3}'.format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.name),
            start_date,
            end_date
        )

        report_type = request.GET.get('type')
        if report_type == 'day-excel':
            return self.create_by_day_excel(
                filename, start_date, end_date,
                request.user, ad_group, filtered_sources,
                conversion_goals
            )
        elif report_type == 'day-csv':
            return self.create_by_day_csv(
                filename, start_date, end_date,
                request.user, ad_group, filtered_sources,
                conversion_goals
            )
        elif report_type == 'content-ad-excel':
            return self.create_by_content_ad_excel(
                filename, start_date, end_date,
                request.user, ad_group, filtered_sources,
                conversion_goals
            )
        elif report_type == 'content-ad-csv':
            return self.create_by_content_ad_csv(
                filename, start_date, end_date,
                request.user, ad_group, filtered_sources,
                conversion_goals
            )

        raise Exception("Invalid report type")

    def create_by_day_csv(self, filename, start_date, end_date, user, ad_group, sources, conversion_goals):
        ads_results = export.generate_rows(
            ['date', 'content_ad'],
            start_date,
            end_date,
            user,
            ignore_diff_rows=True,
            conversion_goals=conversion_goals,
            ad_group=ad_group,
            source=sources
        )

        fieldnames = self._copy_csv_columns(self.common_csv_columns_w_date, user)
        self._add_csv_conversion_goal_columns(fieldnames, conversion_goals)

        content = export.get_csv_content(fieldnames, ads_results)
        return self.create_csv_response(filename, content=content)

    def create_by_day_excel(self, filename, start_date, end_date, user, ad_group, sources, conversion_goals):
        ads_results = export.generate_rows(
            ['date', 'content_ad'],
            start_date,
            end_date,
            user,
            ignore_diff_rows=True,
            conversion_goals=conversion_goals,
            ad_group=ad_group,
            source=sources
        )
        sources_results = export.generate_rows(
            ['date', 'source', 'content_ad'],
            start_date,
            end_date,
            user,
            ignore_diff_rows=True,
            conversion_goals=conversion_goals,
            ad_group=ad_group,
            source=sources
        )

        self.add_source_data(sources_results)

        ads_columns = self._copy_excel_columns(self.common_excel_columns_w_date, user)
        self._add_excel_conversion_goal_columns(ads_columns, conversion_goals)

        sources_columns = list(ads_columns)  # make a shallow copy
        sources_columns.insert(5, {'key': 'source', 'name': 'Source', 'width': 20})

        content = export.get_excel_content([
            ('Detailed Report', ads_columns, ads_results),
            ('Per Source Report', sources_columns, sources_results)
        ])

        return self.create_excel_response(filename, content=content)

    def create_by_content_ad_excel(self, filename, start_date, end_date, user, ad_group, sources, conversion_goals):
        ads_results = export.generate_rows(
            ['content_ad'],
            start_date,
            end_date,
            user,
            ignore_diff_rows=True,
            conversion_goals=conversion_goals,
            ad_group=ad_group,
            source=sources
        )
        sources_results = export.generate_rows(
            ['content_ad', 'source'],
            start_date,
            end_date,
            user,
            ignore_diff_rows=True,
            conversion_goals=conversion_goals,
            ad_group=ad_group,
            source=sources
        )

        self.add_source_data(sources_results)

        ads_columns = self._copy_excel_columns(self.common_excel_columns, user)
        self._add_excel_conversion_goal_columns(ads_columns, conversion_goals)

        sources_columns = list(ads_columns)  # make a shallow copy
        sources_columns.insert(4, {'key': 'source', 'name': 'Source', 'width': 20})

        content = export.get_excel_content([
            ('Detailed Report', ads_columns, ads_results),
            ('Per Source Report', sources_columns, sources_results)
        ])
        return self.create_excel_response(filename, content=content)

    def create_by_content_ad_csv(self, filename, start_date, end_date, user, ad_group, sources, conversion_goals):
        ads_results = export.generate_rows(
            ['content_ad'],
            start_date,
            end_date,
            user,
            ignore_diff_rows=True,
            conversion_goals=conversion_goals,
            ad_group=ad_group,
            source=sources
        )
        fieldnames = self._copy_csv_columns(self.common_csv_columns, user)
        self._add_csv_conversion_goal_columns(fieldnames, conversion_goals)
        content = export.get_csv_content(fieldnames, ads_results)
        return self.create_csv_response(filename, content=content)

    def _copy_excel_columns(self, columns, user):
        columns_copy = []
        include_acq_cols = user.has_perm('zemauth.content_ads_postclick_acquisition')
        include_eng_cols = user.has_perm('zemauth.content_ads_postclick_engagement')
        for col in columns:
            key = col['key']
            if (key in POSTCLICK_ACQUISITION_FIELDS and not include_acq_cols) or\
               (key in POSTCLICK_ENGAGEMENT_FIELDS and not include_eng_cols):
                continue

            columns_copy.append(dict(col))
        return columns_copy

    def _copy_csv_columns(self, columns, user):
        columns_copy = OrderedDict()
        include_acq_cols = user.has_perm('zemauth.content_ads_postclick_acquisition')
        include_eng_cols = user.has_perm('zemauth.content_ads_postclick_engagement')
        for col in columns:
            key = col[0]
            if (key in POSTCLICK_ACQUISITION_FIELDS and not include_acq_cols) or\
               (key in POSTCLICK_ENGAGEMENT_FIELDS and not include_eng_cols):
                continue

            columns_copy[key] = col[1]
        return columns_copy

    def _add_excel_conversion_goal_columns(self, columns, conversion_goals):
        for conversion_goal in conversion_goals:
            columns.append({'key': conversion_goal.get_view_key(conversion_goals), 'name': conversion_goal.name})

    def _add_csv_conversion_goal_columns(self, columns, conversion_goals):
        for conversion_goal in conversion_goals:
            columns[conversion_goal.get_view_key(conversion_goals)] = conversion_goal.name

    def add_source_data(self, results):
        sources = {source.id: source for source in models.Source.objects.all()}

        for result in results:
            result['source'] = sources[result['source']].name


class AdGroupSourcesExport(ExportApiView):
    @influx.timer('dash.export')
    @statsd_helper.statsd_timer('dash.export', 'ad_group_sources_export_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        conversion_goals = []
        if request.user.has_perm('zemauth.conversion_reports'):
            conversion_goals = ad_group.campaign.conversiongoal_set.all()

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        filename = '{0}_{1}_per_sources_report_{2}_{3}'.format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.name),
            start_date,
            end_date
        )

        date_source_results = export.generate_rows(
            ['date', 'source'],
            start_date,
            end_date,
            request.user,
            conversion_goals=conversion_goals,
            ad_group=ad_group,
            source=filtered_sources,
        )

        self.add_source_data(date_source_results)

        if request.GET.get('type') == 'excel':
            date_source_columns = [
                {'key': 'date', 'name': 'Date', 'format': 'date'},
                {'key': 'source', 'name': 'Source', 'width': 30},
                {'key': 'cost', 'name': 'Cost', 'format': 'currency'},
                {'key': 'cpc', 'name': 'Avg. CPC', 'format': 'currency'},
                {'key': 'clicks', 'name': 'Clicks'},
                {'key': 'impressions', 'name': 'Impressions', 'width': 15},
                {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
            ]

            for conversion_goal in conversion_goals:
                date_source_columns.append(
                    {'key': conversion_goal.get_view_key(conversion_goals), 'name': conversion_goal.name}
                )

            sheets_data = [('Per Source Report', date_source_columns, date_source_results)]

            date_results = export.generate_rows(
                ['date'],
                start_date,
                end_date,
                request.user,
                conversion_goals=conversion_goals,
                ad_group=ad_group,
                source=filtered_sources,
            )

            date_columns = list(date_source_columns)  # make a shallow copy
            date_columns.pop(1)

            sheets_data.insert(0, ('Per Day Report', date_columns, date_results))

            content = export.get_excel_content(sheets_data)
            return self.create_excel_response(filename, content=content)
        else:
            fieldnames = OrderedDict([
                ('date', 'Date'),
                ('source', 'Source'),
                ('cost', 'Cost'),
                ('cpc', 'CPC'),
                ('clicks', 'Clicks'),
                ('impressions', 'Impressions'),
                ('ctr', 'CTR')
            ])

            for conversion_goal in conversion_goals:
                fieldnames[conversion_goal.get_view_key(conversion_goals)] = conversion_goal.name

            content = export.get_csv_content(fieldnames, date_source_results)
            return self.create_csv_response(filename, content=content)

    def add_source_data(self, results):
        sources = {source.id: source for source in models.Source.objects.all()}

        for result in results:
            result['source'] = sources[result['source']].name


class AllAccountsExport(ExportApiView):
    def get(self, request):
        accounts = models.Account.objects.all().filter_by_user(request.user)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        filename = 'all_accounts_report_{0}_{1}'.format(start_date, end_date)

        results = export.generate_rows(
            ['date', 'account'],
            start_date,
            end_date,
            request.user,
            account=accounts,
            source=filtered_sources,
        )

        self.add_account_data(results, accounts)

        if request.GET.get('type') == 'excel':
            detailed_results = export.generate_rows(
                ['date', 'account', 'campaign'],
                start_date,
                end_date,
                request.user,
                account=accounts,
                source=filtered_sources,
            )

            self.add_account_data(detailed_results, accounts)
            self.add_campaign_data(detailed_results, accounts)

            columns = [
                {'key': 'date', 'name': 'Date', 'format': 'date'},
                {'key': 'account', 'name': 'Account'},
                {'key': 'cost', 'name': 'Spend', 'format': 'currency'},
                {'key': 'cpc', 'name': 'Avg. CPC', 'format': 'currency'},
                {'key': 'clicks', 'name': 'Clicks'},
                {'key': 'impressions', 'name': 'Impressions', 'width': 15},
                {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
            ]

            detailed_columns = [
                {'key': 'date', 'name': 'Date', 'format': 'date'},
                {'key': 'account', 'name': 'Account'},
                {'key': 'campaign', 'name': 'Campaign'},
                {'key': 'campaign_manager', 'name': 'Campaign Manager'},
                {'key': 'sales_representative', 'name': 'Sales Representative'},
                {'key': 'service_fee', 'name': 'Service Fee', 'format': 'percent'},
                {'key': 'iab_category', 'name': 'IAB Category'},
                {'key': 'promotion_goal', 'name': 'Promotion Goal'},
                {'key': 'cost', 'name': 'Spend', 'format': 'currency'},
                {'key': 'cpc', 'name': 'Avg. CPC', 'format': 'currency'},
                {'key': 'clicks', 'name': 'Clicks'},
                {'key': 'impressions', 'name': 'Impressions', 'width': 15},
                {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
                {'key': 'fee_amount', 'name': 'Fee Amount', 'format': 'currency'},
                {'key': 'total_amount', 'name': 'Total Amount', 'format': 'currency'},
            ]

            content = export.get_excel_content([
                ('All Accounts Report', columns, results),
                ('Detailed Report', detailed_columns, detailed_results)
            ], start_date, end_date)

            return self.create_excel_response(filename, content=content)
        else:
            fieldnames = OrderedDict([
                ('date', 'Date'),
                ('account', 'Account'),
                ('cost', 'Spend'),
                ('cpc', 'CPC'),
                ('clicks', 'Clicks'),
                ('impressions', 'Impressions'),
                ('ctr', 'CTR')
            ])

            content = export.get_csv_content(fieldnames, results, 'All accounts report', start_date, end_date)
            return self.create_csv_response(filename, content=content)

    def add_account_data(self, results, accounts):
        accounts_by_id = {account.id: account.name for account in accounts}
        account_settings_by_id = {account.id: account.get_current_settings() for account in accounts}

        for result in results:
            account_id = result['account']
            result['account'] = accounts_by_id[account_id]
            result['service_fee'] = (float(account_settings_by_id[account_id].service_fee) if
                                     account_settings_by_id.get(account_id) else 'N/A')

    def add_campaign_data(self, results, accounts):
        campaign_names = {campaign.id: campaign.name for campaign in
                          models.Campaign.objects.filter(account=accounts)}

        settings_queryset = models.CampaignSettings.objects\
                                                   .filter(campaign__account=accounts)\
                                                   .group_current_settings()

        campaign_settings = {s.campaign.id: s for s in settings_queryset}

        for result in results:
            campaign_id = result['campaign']
            cs = campaign_settings.get(campaign_id)
            sales_representative = cs.campaign.get_sales_representative() if cs is not None else None

            has_service_fee = result.get('service_fee') and result['service_fee'] != 'N/A'
            cost = result['cost'] or 0
            result['campaign'] = campaign_names[campaign_id]
            result['campaign_manager'] = cs.campaign_manager.email if cs is not None and cs.campaign_manager is not None else 'N/A'
            result['sales_representative'] = sales_representative.email if sales_representative is not None else 'N/A'
            result['iab_category'] = cs.iab_category if cs is not None else 'N/A'
            result['promotion_goal'] = constants.PromotionGoal.get_text(cs.promotion_goal) if cs is not None else 'N/A'
            result['fee_amount'] = (cost / (1.0 - result['service_fee'])) - cost if has_service_fee else 'N/A'
            result['total_amount'] = cost + result['fee_amount'] if has_service_fee else 'N/A'
