#!/usr/bin/python
# -*- coding: utf-8 -*-

import slugify

from collections import OrderedDict

from django.conf import settings

from dash.views import helpers
from dash import models
from dash import export
from utils import api_common
from utils import statsd_helper

# DAVORIN TODO:
# Go through all todos,
# Un-commit table.py
# check if all works
# fix Tests
# write tests and e2e tests


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
        # DAVORIN TODO Demo
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
    @statsd_helper.statsd_timer('dash.export', 'accounts_campaigns_export_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        export_type = request.GET.get('type')

        user = request.user

        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))

        order = request.GET.get('order') or 'name'

        if export_type == 'view-csv':
            filename = '{0}_report_{1}_{2}'.format(
                slugify.slugify(account.name),
                start_date,
                end_date
            )
            content = export.AccountCampaignsExport().get_data(user, account_id, filtered_sources, start_date, end_date, order, additional_fields)
        elif export_type == 'adgroup-csv':
            filename = '{0}_-_by_ad_group_report_{1}_{2}'.format(
                slugify.slugify(account.name),
                start_date,
                end_date
            )
            content = export.AccountCampaignsExport().get_data(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group')
        elif export_type == 'contentad-csv':
            filename = '{0}_-_by_content_ad_report_{1}_{2}'.format(
                slugify.slugify(account.name),
                start_date,
                end_date
            )
            content = export.AccountCampaignsExport().get_data(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad')

        return self.create_csv_response(filename, content=content)


class CampaignAdGroupsExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export', 'campaigns_ad_groups_export_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        export_type = request.GET.get('type')

        user = request.user

        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))

        order = request.GET.get('order') or 'name'

        if export_type == 'view-csv':
            filename = '{0}_{1}_report_{2}_{3}'.format(
                slugify.slugify(campaign.account.name),
                slugify.slugify(campaign.name),
                start_date,
                end_date
            )
            content = export.CampaignAdGroupsExport().get_data(user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields)
        elif export_type == 'contentad-csv':
            filename = '{0}_{1}_-_by_content_ad_report_{2}_{3}'.format(
                slugify.slugify(campaign.account.name),
                slugify.slugify(campaign.name),
                start_date,
                end_date
            )
            content = export.CampaignAdGroupsExport().get_data(user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad')

        return self.create_csv_response(filename, content=content)


class AdGroupAdsExportAllowed(api_common.BaseApiView):
    # DAVORIN TODO Remove
    MAX_ROWS = 16134

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


class AdGroupAdsPlusExportAllowed(api_common.BaseApiView):
    # DAVORIN TODO Remove, also remove from urls
    MAX_ROWS = 16134

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


class ExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 16134

    @statsd_helper.statsd_timer('dash.export', 'ad_group_ads_plus_export_allowed_get')
    def get(self, request, id_, level_):
        user = request.user

        if level_ == 'ad_groups':
            ad_group = helpers.get_ad_group(user, id_)
            return self.create_api_response({
                'view': models.ContentAd.objects.filter(ad_group=ad_group).count() <= self.MAX_ROWS
            })
        elif level_ == 'campaigns':
            campaign = helpers.get_campaign(user, id_)
            ad_groups = models.AdGroup.objects.filter(campaign=campaign)
            return self.create_api_response({
                'view': ad_groups.count() <= self.MAX_ROWS,
                'content_ad': models.ContentAd.objects.filter(ad_group=ad_groups).count() <= self.MAX_ROWS
            })
        elif level_ == 'accounts':
            account = helpers.get_account(user, id_)
            campaigns = models.Campaign.objects.filter(account=account)
            ad_groups = models.AdGroup.objects.filter(campaign=campaigns)
            return self.create_api_response({
                'view': campaigns.count() <= self.MAX_ROWS,
                'ad_group': ad_groups.count() <= self.MAX_ROWS,
                'content_ad': models.ContentAd.objects.filter(ad_group=ad_groups).count() <= self.MAX_ROWS
            })
        elif level_ == 'all_accounts':
            accounts_num = models.Account.objects.all().filter_by_user(user).count()
            campaigns_num = models.Campaign.objects.all().filter_by_user(user).count()
            ad_groups_num = models.AdGroup.objects.all().filter_by_user(user).count()
            return self.create_api_response({
                'view': accounts_num <= self.MAX_ROWS,
                'campaign': campaigns_num <= self.MAX_ROWS,
                'ad_group': ad_groups_num <= self.MAX_ROWS
            })

        return self.create_api_response({
            'view': True
        })


class SourcesExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 16134

    @statsd_helper.statsd_timer('dash.export', 'ad_group_ads_plus_export_allowed_get')
    def get(self, request, id_, level_):
        user = request.user
        filtered_sources_num = len(helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources')))
        if level_ == 'ad_groups':
            ad_group = helpers.get_ad_group(user, id_)
            return self.create_api_response({
                'view': filtered_sources_num <= self.MAX_ROWS,
                'content_ad': models.ContentAd.objects.filter(ad_group=ad_group).count() * filtered_sources_num <= self.MAX_ROWS
            })
        elif level_ == 'campaigns':
            campaign = helpers.get_campaign(user, id_)
            ad_groups = models.AdGroup.objects.filter(campaign=campaign)
            return self.create_api_response({
                'view': filtered_sources_num <= self.MAX_ROWS,
                'ad_group': ad_groups.count() * filtered_sources_num <= self.MAX_ROWS,
                'content_ad': models.ContentAd.objects.filter(ad_group__in=ad_groups).count() * filtered_sources_num <= self.MAX_ROWS
            })
        elif level_ == 'accounts':
            account = helpers.get_account(user, id_)
            campaigns = models.Campaign.objects.filter(account=account)
            ad_groups = models.AdGroup.objects.filter(campaign=campaigns)
            return self.create_api_response({
                'view': filtered_sources_num <= self.MAX_ROWS,
                'campaign': campaigns.count() * filtered_sources_num <= self.MAX_ROWS,
                'ad_group': ad_groups.count() * filtered_sources_num <= self.MAX_ROWS,
                'content_ad': models.ContentAd.objects.filter(ad_group__in=ad_groups).count() * filtered_sources_num <= self.MAX_ROWS
            })
        elif level_ == 'all_accounts':
            accounts_num = models.Account.objects.all().filter_by_user(user).count()
            campaigns_num = models.Campaign.objects.all().filter_by_user(user).count()
            ad_groups_num = models.AdGroup.objects.all().filter_by_user(user).count()
            return self.create_api_response({
                'view': filtered_sources_num <= self.MAX_ROWS,
                'account': accounts_num * filtered_sources_num <= self.MAX_ROWS,
                'campaign': campaigns_num * filtered_sources_num <= self.MAX_ROWS,
                'ad_group': ad_groups_num * filtered_sources_num <= self.MAX_ROWS
            })

        return self.create_api_response({
            'view': True
        })


class CampaignAdGroupsExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 8072

    @statsd_helper.statsd_timer('dash.export', 'campiagn_ad_group_export_allowed_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)
        print 'laalalalalalalalalalaala'
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


class AdGroupAdsExport(ExportApiView):
    # TODO DAVORIN REMOVE also url
    @statsd_helper.statsd_timer('dash.export', 'ad_group_ads_export_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        filename = '{0}_{1}_detailed_report_{2}_{3}'.format(
            slugify.slugify(ad_group.campaign.account.name),
            slugify.slugify(ad_group.name),
            start_date,
            end_date
        )

        ads_results = export.generate_rows(
            ['date', 'article'],
            start_date,
            end_date,
            request.user,
            ad_group=ad_group,
            source=filtered_sources,
        )

        if request.GET.get('type') == 'excel':
            sources_results = export.generate_rows(
                ['date', 'source', 'article'],
                start_date,
                end_date,
                request.user,
                ad_group=ad_group,
                source=filtered_sources,
            )

            self.add_source_data(sources_results)

            ads_columns = [
                {'key': 'date', 'name': 'Date', 'format': 'date'},
                {'key': 'title', 'name': 'Title', 'width': 30},
                {'key': 'url', 'name': 'URL', 'width': 40},
                {'key': 'cost', 'name': 'Cost', 'format': 'currency'},
                {'key': 'cpc', 'name': 'Avg. CPC', 'format': 'currency'},
                {'key': 'clicks', 'name': 'Clicks'},
                {'key': 'impressions', 'name': 'Impressions', 'width': 15},
                {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
            ]

            sources_columns = list(ads_columns)  # make a shallow copy
            sources_columns.insert(3, {'key': 'source', 'name': 'Source', 'width': 20})

            content = export.get_excel_content([
                ('Detailed Report', ads_columns, ads_results),
                ('Per Source Report', sources_columns, sources_results)
            ])

            return self.create_excel_response(filename, content=content)
        else:
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

            content = export.get_csv_content(fieldnames, ads_results)
            return self.create_csv_response(filename, content=content)

    def add_source_data(self, results):
        sources = {source.id: source for source in models.Source.objects.all()}

        for result in results:
            result['source'] = sources[result['source']].name


class AdGroupAdsPlusExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export', 'ad_group_ads_plus_export_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        export_type = request.GET.get('type')
        user = request.user
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'

        if export_type == 'view-csv':
            filename = '{0}_{1}_{2}_report_{3}_{4}'.format(
                slugify.slugify(ad_group.campaign.account.name),
                slugify.slugify(ad_group.campaign.name),
                slugify.slugify(ad_group.name),
                start_date,
                end_date
            )
            content = export.AdGroupAdsPlusExport().get_data(user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields)
        return self.create_csv_response(filename, content=content)


class AllAccountsSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export', 'account_sources_export_get')
    def get(self, request):
        user = request.user
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'
        export_type = request.GET.get('type')

        if export_type == 'view-csv':
            filename = 'ZemantaOne_media_source_report_{0}_{1}'.format(
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_all_accounts(user, filtered_sources, start_date, end_date, order, additional_fields,)
        elif export_type == 'account-csv':
            filename = 'ZemantaOne_-_by_account_media_source_report_{0}_{1}'.format(
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_all_accounts(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='account')
        elif export_type == 'campaign-csv':
            filename = 'ZemantaOne_-_by_campaign_media_source_report_{0}_{1}'.format(
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_all_accounts(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='campaign')
        elif export_type == 'adgroup-csv':
            filename = 'ZemantaOne_-_by_ad_group_media_source_report_{0}_{1}'.format(
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_all_accounts(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group')
        return self.create_csv_response(filename, content=content)


class AccountSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export', 'account_sources_export_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)
        user = request.user
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'
        export_type = request.GET.get('type')

        if export_type == 'view-csv':
            filename = '{0}_media_source_report_{1}_{2}'.format(
                slugify.slugify(account.name),
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_account(user, account_id, filtered_sources, start_date, end_date, order, additional_fields)
        elif export_type == 'campaign-csv':
            filename = '{0}_-_by_campaign_media_source_report_{1}_{2}'.format(
                slugify.slugify(account.name),
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_account(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='campaign')
        elif export_type == 'adgroup-csv':
            filename = '{0}_-_by_ad_group_media_source_report_{1}_{2}'.format(
                slugify.slugify(account.name),
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_account(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group')
        elif export_type == 'contentad-csv':
            filename = '{0}_-_by_content_ad_media_source_report_{1}_{2}'.format(
                slugify.slugify(account.name),
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_account(user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad')

        return self.create_csv_response(filename, content=content)


class CampaignSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export', 'campaign_sources_export_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        user = request.user

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))

        order = request.GET.get('order') or 'name'

        export_type = request.GET.get('type')

        if export_type == 'view-csv':
            filename = '{0}_{1}_media_source_report_{2}_{3}'.format(
                slugify.slugify(campaign.account.name),
                slugify.slugify(campaign.name),
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_campaign(user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields)
        elif export_type == 'adgroup-csv':
            filename = '{0}_{1}_-_by_ad_group_media_source_report_{2}_{3}'.format(
                slugify.slugify(campaign.account.name),
                slugify.slugify(campaign.name),
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_campaign(user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group')
        elif export_type == 'contentad-csv':
            filename = '{0}_{1}_-_by_content_ad_media_source_report_{2}_{3}'.format(
                slugify.slugify(campaign.account.name),
                slugify.slugify(campaign.name),
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_campaign(user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad')

        return self.create_csv_response(filename, content=content)


class AdGroupSourcesExport(ExportApiView):
    @statsd_helper.statsd_timer('dash.export', 'ad_group_sources_export_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)
        user = request.user
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))
        order = request.GET.get('order') or 'name'
        export_type = request.GET.get('type')

        if export_type == 'view-csv':
            filename = '{0}_{1}_{2}_media_source_report_{3}_{4}'.format(
                slugify.slugify(ad_group.campaign.account.name),
                slugify.slugify(ad_group.campaign.name),
                slugify.slugify(ad_group.name),
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_ad_group(user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields)
        elif export_type == 'contentad-csv':
            filename = '{0}_{1}_{2}_-_by_content_ad_media_source_report_{3}_{4}'.format(
                slugify.slugify(ad_group.campaign.account.name),
                slugify.slugify(ad_group.campaign.name),
                slugify.slugify(ad_group.name),
                start_date,
                end_date
            )
            content = export.SourcesExport().get_data_ad_group(user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown='content_ad')
        return self.create_csv_response(filename, content=content)


class AllAccountsExport(ExportApiView):
    def get(self, request):
        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))

        user = request.user

        additional_fields = helpers.get_additional_columns(request.GET.get('additional_fields'))

        order = request.GET.get('order') or 'name'

        export_type = request.GET.get('type')

        if export_type == 'view-csv':
            filename = 'ZemantaOne_report_{0}_{1}'.format(start_date, end_date)
            content = export.AllAccountsExport().get_data(user, filtered_sources, start_date, end_date, order, additional_fields)
        elif export_type == 'campaign-csv':
            filename = 'ZemantaOne_-_by_campaign_report_{0}_{1}'.format(start_date, end_date)
            content = export.AllAccountsExport().get_data(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='campaign')
        elif export_type == 'adgroup-csv':
            filename = 'ZemantaOne_-_by_ad_group_report_{0}_{1}'.format(start_date, end_date)
            content = export.AllAccountsExport().get_data(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown='ad_group')

        return self.create_csv_response(filename, content=content)
