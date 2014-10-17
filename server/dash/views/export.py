import slugify

from collections import OrderedDict

from dash.views import helpers
from dash import models
from dash import export
from dash import constants
from utils import api_common
from utils import statsd_helper


class AccountCampaignsExport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('dash.api', 'accounts_campaigns_export_get')
    def get(self, request, account_id):
        account = helpers.get_account(request.user, account_id)

        campaigns = models.Campaign.objects.get_for_user(request.user).filter(account=account)

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

        filename = '{0}_{1}_per_campaign_report_{2}_{3}'.format(
            slugify.slugify(campaign.account.name),
            slugify.slugify(campaign.name),
            start_date,
            end_date
        )

        data = export.generate_rows(
            ['date'],
            start_date,
            end_date,
            request.user,
            campaign=campaign
        )

        if request.GET.get('type') == 'excel':
            detailed_data = export.generate_rows(
                ['date', 'ad_group'],
                start_date,
                end_date,
                request.user,
                campaign=campaign
            )

            self.add_ad_group_data(detailed_data, campaign)

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

            content = export.get_excel_content([
                ('Per Campaign Report', columns, data),
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

    def add_ad_group_data(self, results, campaign):
        ad_groups = {ad_group.id: ad_group for ad_group in models.AdGroup.objects.filter(campaign=campaign)}

        for result in results:
            result['ad_group'] = ad_groups[result['ad_group']].name


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
        accounts = models.Account.objects.get_for_user(request.user)

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
                {'key': 'cost', 'name': 'Cost', 'format': 'currency'},
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
                {'key': 'service_fee', 'name': 'Service Fee', 'format': 'currency'},
                {'key': 'iab_category', 'name': 'IAB Category'},
                {'key': 'promotion_goal', 'name': 'Promotion Goal'},
                {'key': 'cost', 'name': 'Cost', 'format': 'currency'},
                {'key': 'cpc', 'name': 'Avg. CPC', 'format': 'currency'},
                {'key': 'clicks', 'name': 'Clicks'},
                {'key': 'impressions', 'name': 'Impressions', 'width': 15},
                {'key': 'ctr', 'name': 'CTR', 'format': 'percent'},
            ]

            content = export.get_excel_content([
                ('All Accounts Report', columns, results),
                ('Detailed Report', detailed_columns, detailed_results)
            ])

            return self.create_excel_response(filename, content=content)
        else:
            fieldnames = OrderedDict([
                ('date', 'Date'),
                ('account', 'Account'),
                ('cost', 'Cost'),
                ('cpc', 'CPC'),
                ('clicks', 'Clicks'),
                ('impressions', 'Impressions'),
                ('ctr', 'CTR')
            ])

            content = export.get_csv_content(fieldnames, results)
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
            cs = campaign_settings[campaign_id]

            result['campaign'] = campaign_names[campaign_id]
            result['account_manager'] = cs.account_manager.email if cs.account_manager is not None else 'N/A'
            result['sales_representative'] = cs.sales_representative.email if cs.sales_representative is not None else 'N/A'
            result['service_fee'] = cs.service_fee
            result['iab_category'] = cs.iab_category
            result['promotion_goal'] = constants.PromotionGoal.get_text(cs.promotion_goal)
