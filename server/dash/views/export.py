import slugify

from collections import OrderedDict

from dash.views import helpers
from dash import models
from dash import export
from dash import constants
from utils import api_common
from utils import statsd_helper
from utils.sort_helper import sort_results
from utils import exc


class AccountCampaignsExport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'accounts_campaigns_export_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)

        campaigns = models.Campaign.objects.all().filter_by_user(request.user).filter(account=account)

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
            campaign=campaigns
        )

        if request.GET.get('type') == 'excel':
            detailed_data = export.generate_rows(
                ['date', 'campaign'],
                start_date,
                end_date,
                request.user,
                campaign=campaigns
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


class CampaignAdGroupsExport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'campaigns_ad_groups_export_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

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
            campaign=campaign
        )

        if export_type == 'excel' or export_type == 'excel_detailed':
            detailed_data = export.generate_rows(
                ['date', 'ad_group'],
                start_date,
                end_date,
                request.user,
                campaign=campaign
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

            detailed_columns = list(columns)  # make a copy
            detailed_columns.insert(1, {'key': 'ad_group', 'name': 'Ad Group', 'width': 30})

            sheets = [
                ('Per Campaign Report', columns, data),
                ('Detailed Report', detailed_columns, detailed_data)
            ]

            if export_type == 'excel_detailed':
                filename_format = '{0}_{1}_per_campaign_detailed_report_{2}_{3}'

                per_content_ad_data = export.generate_rows(
                    ['date', 'ad_group', 'article'],
                    start_date,
                    end_date,
                    request.user,
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


class AdGroupAdsExportAllowed(api_common.BaseApiView):
    MAX_ROWS = 16134

    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_export_allowed_get')
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

    @statsd_helper.statsd_timer('dash.api', 'campiagn_ad_group_export_allowed_get')
    def get(self, request, campaign_id):
        campaign = helpers.get_ad_group(request.user, campaign_id)

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


class AdGroupAdsExport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_ads_export_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

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
            ad_group=ad_group
        )

        if request.GET.get('type') == 'excel':
            sources_results = export.generate_rows(
                ['date', 'source', 'article'],
                start_date,
                end_date,
                request.user,
                ad_group=ad_group
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


class AdGroupSourcesExport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'ad_group_sources_export_get')
    def get(self, request, ad_group_id):
        ad_group = helpers.get_ad_group(request.user, ad_group_id)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

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
            ad_group=ad_group
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

            sheets_data = [('Per Source Report', date_source_columns, date_source_results)]

            if request.user.has_perm('reports.per_day_sheet_source_export'):
                date_results = export.generate_rows(
                    ['date'],
                    start_date,
                    end_date,
                    request.user,
                    ad_group=ad_group
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

            content = export.get_csv_content(fieldnames, date_source_results)
            return self.create_csv_response(filename, content=content)

    def add_source_data(self, results):
        sources = {source.id: source for source in models.Source.objects.all()}

        for result in results:
            result['source'] = sources[result['source']].name


class AllAccountsExport(api_common.BaseApiView):
    def get(self, request):
        accounts = models.Account.objects.all().filter_by_user(request.user)

        start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
        end_date = helpers.get_stats_end_date(request.GET.get('end_date'))

        filename = 'all_accounts_report_{0}_{1}'.format(start_date, end_date)

        results = export.generate_rows(
            ['date', 'account'],
            start_date,
            end_date,
            request.user,
            account=accounts
        )

        self.add_account_data(results, accounts)

        if request.GET.get('type') == 'excel':
            detailed_results = export.generate_rows(
                ['date', 'account', 'campaign'],
                start_date,
                end_date,
                request.user,
                account=accounts
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
                {'key': 'account_manager', 'name': 'Account Manager'},
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
        account_names = {account.id: account.name for account in accounts}

        for result in results:
            result['account'] = account_names[result['account']]

    def add_campaign_data(self, results, accounts):
        campaign_names = {campaign.id: campaign.name for campaign in
                          models.Campaign.objects.filter(account=accounts)}

        settings_queryset = models.CampaignSettings.objects.\
            distinct('campaign').\
            filter(campaign__account=accounts).\
            order_by('campaign', '-created_dt')

        campaign_settings = {s.campaign.id: s for s in settings_queryset}

        for result in results:
            campaign_id = result['campaign']
            cs = campaign_settings.get(campaign_id)

            result['campaign'] = campaign_names[campaign_id]
            result['account_manager'] = cs.account_manager.email if cs is not None and cs.account_manager is not None else 'N/A'
            result['sales_representative'] = cs.sales_representative.email if cs is not None and cs.sales_representative is not None else 'N/A'
            result['service_fee'] = float(cs.service_fee) if cs is not None else 'N/A'
            result['iab_category'] = cs.iab_category if cs is not None else 'N/A'
            result['promotion_goal'] = constants.PromotionGoal.get_text(cs.promotion_goal) if cs is not None else 'N/A'
            result['fee_amount'] = result['cost'] * result['service_fee'] if cs is not None else 'N/A'
            result['total_amount'] = result['cost'] + result['fee_amount'] if cs is not None else 'N/A'
