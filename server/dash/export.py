import unicodecsv
from xlsxwriter import Workbook
import StringIO
from collections import OrderedDict

from dash import models
from dash import stats_helper
from dash import table
from dash.views import helpers

import reports.api
import reports.api_contentads
import reports.api_helpers

from utils.sort_helper import sort_results

FIELDNAMES = {
    'start_date': 'Start Date',
    'end_date': 'End Date',
    'account': 'Account',
    'campaign': 'Campaign',
    'ad_group': 'Ad Group',
    'cost': 'Spend',
    'cpc': 'Average CPC',
    'clicks': 'Clicks',
    'impressions': 'Impressions',
    'ctr': 'CTR',
    'ctr': 'CTR',
    'visits': 'Visits',
    'click_discrepancy': 'Click Discrepancy',
    'pageviews': 'Pageviews',
    'percent_new_users': 'Percent New Users',
    'bounce_rate': 'Bounce Rate',
    'pv_per_visit': 'PV/Visit',
    'avg_tos': 'Avg. ToS',
    'budget': 'Total Budget',
    'available_budget': 'Available Budget',
    'unspent_budget': 'Unspent Budget',
    'urlLink': 'URL',
    'image_urls': 'Image URL',
    'upload_time': 'Uploaded',
    'batch_name': 'Batch Name',
    'display_url': 'Display URL',
    'brand_name': 'Brand Name',
    'description': 'Description',
    'call_to_action': 'Call to action',
    'title': 'Title',
    'source': 'Source'
}

UNEXPORTABLE_FIELDS = ['last_sync', 'supply_dash_url', 'state',
                       'submission_status', 'titleLink', 'bid_cpc',
                       'min_bid_cpc', 'max_bid_cpc', 'current_bid_cpc',
                       'daily_budget', 'current_daily_budget', 'yesterday_cost']


def _get_content_ads(constraints):
    sources = None
    fields = {}

    for key in constraints:
        if key == 'source':
            sources = constraints[key]
        elif key == 'campaign':
            fields['ad_group__campaign'] = constraints[key]
        else:
            fields[key] = constraints[key]

    content_ads = models.ContentAd.objects.filter(**fields).select_related('batch')

    if sources is not None:
        content_ads = content_ads.filter_by_sources(sources)

    return {c.id: c for c in content_ads}


def _generate_content_ad_rows(dimensions, start_date, end_date, user, ordering, ignore_diff_rows, conversion_goals, **constraints):
    content_ads = _get_content_ads(constraints)

    stats = stats_helper.get_content_ad_stats_with_conversions(
        user,
        start_date,
        end_date,
        breakdown=dimensions,
        ignore_diff_rows=ignore_diff_rows,
        conversion_goals=conversion_goals,
        constraints=constraints
    )

    for stat in stats:
        content_ad = content_ads[stat['content_ad']]
        stat['title'] = content_ad.title
        stat['url'] = content_ad.url
        stat['image_url'] = content_ad.get_image_url()
        stat['uploaded'] = content_ad.created_dt.date()
        if 'source' in stat:
            stat['source'] = models.Source.objects.get(id=stat['source']).name
        for goal in conversion_goals:
            stat[goal.name] = stat.pop(goal.get_view_key())

    return sort_results(stats, ordering)


def get_csv_content(fieldnames, data, title_text=None, include_header=True):
    output = StringIO.StringIO()
    if title_text is not None:
        output.write('# {0}\n\n'.format(title_text))

    writer = unicodecsv.DictWriter(output, fieldnames, encoding='utf-8', dialect='excel')

    # header
    if include_header:
        writer.writerow(fieldnames)

    for item in data:
        # Format
        row = {}
        for key in fieldnames.keys():
            value = item.get(key)

            if not value:
                value = 0

            if value and key in ['ctr', 'click_discrepancy', 'percent_new_users', 'bounce_rate', 'pv_per_visit', 'avg_tos']:
                value = '{:.2f}'.format(value)

            row[key] = value
            if repr(value).find(';') != -1:
                row[key] = '"' + value + '"'

        writer.writerow(row)

    return output.getvalue()


def _get_fieldnames(required_fields, additional_fields, name_text):
    fields = [field for field in (required_fields + additional_fields) if field not in UNEXPORTABLE_FIELDS]
    fieldnames = OrderedDict([(k, FIELDNAMES.get(k) or k) for k in fields])
    if 'name' in fieldnames:
        fieldnames['name'] = name_text
    return fieldnames


def _exclude_fieldnames(fieldnames, exclude):
    return [field for field in fieldnames if field not in exclude]


class AllAccountsExport(object):
    def get_data_current_view(self, user, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        results = table.AccountsAccountsTable().get(
            user,
            filtered_sources,
            start_date,
            end_date,
            order,
            1,
            4294967295,
            include_archived
        ).get('rows')

        required_fields = ['start_date', 'end_date', 'name']
        fieldnames = _get_fieldnames(required_fields, additional_fields, 'Account')

        for row in results:
            row['start_date'] = start_date
            row['end_date'] = end_date
        return get_csv_content(fieldnames, results, include_header=include_header)

    def get_data_by_campaign(self, user, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        for account in models.Account.objects.all().filter_by_user(user).filter_by_sources(filtered_sources):
            final_results = final_results + AccountCampaignsExport().get_data_current_view(
                user,
                account.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header,
                include_archived=include_archived)
            include_header = False
        return final_results

    def get_data_by_ad_group(self, user, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        for account in models.Account.objects.all().filter_by_user(user).filter_by_sources(filtered_sources):
            final_results = final_results + AccountCampaignsExport().get_data_by_ad_group(
                user,
                account.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header,
                include_archived=include_archived)
            include_header = False
        return final_results


class AccountCampaignsExport(object):
    def get_data_current_view(self, user, account_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        account = helpers.get_account(user, account_id)

        results = table.AccountCampaignsTable().get(
            user,
            account_id,
            filtered_sources,
            start_date,
            end_date,
            order,
            include_archived,
            return_rows_only=True
        )

        required_fields = ['start_date', 'end_date', 'account', 'name']
        fieldnames = _get_fieldnames(required_fields, additional_fields, 'Campaign')
        for row in results:
            row['start_date'] = start_date
            row['end_date'] = end_date
            row['account'] = account.name

        return get_csv_content(fieldnames, results, include_header=include_header)

    def get_data_by_ad_group(self, user, account_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        account = helpers.get_account(user, account_id)
        campaigns = models.Campaign.objects.filter(account=account).filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            campaigns = campaigns.exclude_archived()
        additional_fields = _exclude_fieldnames(additional_fields, ['budget', 'available_budget', 'unspent_budget'])
        for campaign in campaigns:
            print campaign.name  # DAVORIN
            final_results = final_results + CampaignAdGroupsExport().get_data_current_view(
                user,
                campaign.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header,
                include_archived=include_archived)
            include_header = False
        return final_results

    def get_data_by_content_ad(self, user, account_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        account = helpers.get_account(user, account_id)
        campaigns = models.Campaign.objects.filter(account=account).filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            campaigns = campaigns.exclude_archived()
        additional_fields = _exclude_fieldnames(additional_fields, ['budget', 'available_budget', 'unspent_budget'])
        for campaign in campaigns:
            print campaign.name  # DAVORIN
            final_results = final_results + CampaignAdGroupsExport().get_data_by_content_ads(
                user,
                campaign.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header,
                include_archived=include_archived)
            include_header = False
        return final_results


class CampaignAdGroupsExport(object):
    def get_data_current_view(self, user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        campaign = helpers.get_campaign(user, campaign_id)

        results = table.CampaignAdGroupsTable().get(
            user,
            campaign_id,
            filtered_sources,
            start_date,
            end_date,
            order,
            include_archived,
            return_rows_only=True
        )

        required_fields = ['start_date', 'end_date', 'account', 'campaign', 'name']
        fieldnames = _get_fieldnames(required_fields, additional_fields, 'Ad Group')

        for row in results:
            row['start_date'] = start_date
            row['end_date'] = end_date
            row['account'] = campaign.account.name
            row['campaign'] = campaign.name

        if user.has_perm('zemauth.conversion_reports'):
            conversion_goals = campaign.conversiongoal_set.all()
            for conversion_goal in conversion_goals:
                fieldnames[conversion_goal.get_view_key()] = conversion_goal.name

        return get_csv_content(fieldnames, results, include_header=include_header)

    def get_data_by_content_ads(self, user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        campaign = helpers.get_campaign(user, campaign_id)
        adgroups = models.AdGroup.objects.filter(campaign=campaign).filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            adgroups = adgroups.exclude_archived()
        for adgroup in adgroups:
            print 'adg: ', adgroup.name  # DAVORIN
            final_results = final_results + AdGroupAdsPlusExport().get_data_current_view(
                user,
                adgroup.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header,
                include_archived=include_archived)
            include_header = False
        return final_results


class SourcesExport(object):
    def get_data_current_view(self, user, level_, id_, filtered_sources, start_date, end_date, order, additional_fields, include_header=True):

        results = table.SourcesTable().get(
            user,
            level_,
            filtered_sources,
            start_date,
            end_date,
            order,
            id_
        ).get('rows')

        required_fields = ['start_date', 'end_date']
        conversion_goals = []
        if level_ == 'accounts':
            required_fields.extend(['account'])
            account_name = helpers.get_account(user, id_).name
        elif level_ == 'campaigns':
            required_fields.extend(['account', 'campaign'])
            campaign = helpers.get_campaign(user, id_)
            campaign_name = campaign.name
            account_name = campaign.account.name
            if user.has_perm('zemauth.conversion_reports'):
                conversion_goals = campaign.conversiongoal_set.all()
        elif level_ == 'ad_groups':
            required_fields.extend(['account', 'campaign', 'ad_group'])
            ad_group = helpers.get_ad_group(user, id_)
            ad_group_name = ad_group.name
            campaign_name = ad_group.campaign.name
            account_name = ad_group.campaign.account.name
            if user.has_perm('zemauth.conversion_reports'):
                conversion_goals = ad_group.campaign.conversiongoal_set.all()

        required_fields.extend(['name'])
        fieldnames = _get_fieldnames(required_fields, additional_fields, 'Source')

        for row in results:
            row['start_date'] = start_date
            row['end_date'] = end_date
            if 'account' in required_fields:
                row['account'] = account_name
            if 'campaign' in required_fields:
                row['campaign'] = campaign_name
            if 'ad_group' in required_fields:
                row['ad_group'] = ad_group_name

        for conversion_goal in conversion_goals:
            if conversion_goal.get_view_key() in fieldnames:
                fieldnames[conversion_goal.get_view_key()] = conversion_goal.name

        return get_csv_content(fieldnames, results, include_header=include_header)

    def get_data_all_accounts_by_accounts(self, user, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        accounts = models.Account.objects.all().filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            accounts = accounts.exclude_archived()
        for account in accounts:
            print account.name  # DAVORIN
            final_results = final_results + SourcesExport().get_data_current_view(
                user,
                'accounts',
                account.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header)
            include_header = False
        return final_results

    def get_data_all_accounts_by_campaigns(self, user, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        accounts = models.Account.objects.all().filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            accounts = accounts.exclude_archived()
        for account in accounts:
            print account.name  # DAVORIN
            final_results = final_results + SourcesExport().get_data_account_by_campaigns(
                user,
                account.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header,
                include_archived=include_archived)
            include_header = False
        return final_results

    def get_data_all_accounts_by_ad_groups(self, user, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        accounts = models.Account.objects.all().filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            accounts = accounts.exclude_archived()
        for account in accounts:
            print account.name  # DAVORIN
            final_results = final_results + SourcesExport().get_data_account_by_ad_groups(
                user,
                account.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header,
                include_archived=include_archived)
            include_header = False
        return final_results

    def get_data_account_by_campaigns(self, user, account_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        account = helpers.get_account(user, account_id)
        campaigns = models.Campaign.objects.filter(account=account).filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            campaigns = campaigns.exclude_archived()
        for campaign in campaigns:
            print campaign.name  # DAVORIN
            final_results = final_results + SourcesExport().get_data_current_view(
                user,
                'campaigns',
                campaign.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header)
            include_header = False
        return final_results

    def get_data_account_by_ad_groups(self, user, account_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        account = helpers.get_account(user, account_id)
        campaigns = models.Campaign.objects.filter(account=account).filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            campaigns = campaigns.exclude_archived()
        for campaign in campaigns:
            print 'camp: ', campaign.name  # DAVORIN
            final_results = final_results + self.get_data_campaign_by_ad_groups(
                user,
                campaign.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header,
                include_archived=include_archived)
            include_header = False
        return final_results

    def get_data_account_by_content_ads(self, user, account_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        account = helpers.get_account(user, account_id)
        campaigns = models.Campaign.objects.filter(account=account).filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            campaigns = campaigns.exclude_archived()
        for campaign in campaigns:
            print 'camp: ', campaign.name  # DAVORIN
            final_results = final_results + self.get_data_campaign_by_content_ads(
                user,
                campaign.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header,
                include_archived=include_archived)
            include_header = False
        return final_results

    def get_data_campaign_by_ad_groups(self, user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        campaign = helpers.get_campaign(user, campaign_id)
        adgroups = models.AdGroup.objects.filter(campaign=campaign).filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            adgroups = adgroups.exclude_archived()
        for adgroup in adgroups:
            print 'adg: ', adgroup.name  # DAVORIN
            final_results = final_results + SourcesExport().get_data_current_view(
                user,
                'ad_groups',
                adgroup.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header)
            include_header = False
        return final_results

    def get_data_campaign_by_content_ads(self, user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):
        final_results = ''
        campaign = helpers.get_campaign(user, campaign_id)
        adgroups = models.AdGroup.objects.filter(campaign=campaign).filter_by_user(user).filter_by_sources(filtered_sources)
        if not include_archived or not user.has_perm('zemauth.view_archived_entities'):
            adgroups = adgroups.exclude_archived()
        for adgroup in adgroups:
            print 'adg: ', adgroup.name  # DAVORIN
            final_results = final_results + self.get_data_ad_group_by_content_ads(
                user,
                adgroup.id,
                filtered_sources,
                start_date,
                end_date,
                order,
                additional_fields,
                include_header=include_header)
            include_header = False
        return final_results

    def get_data_ad_group_by_content_ads(self, user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True):
        ad_group = helpers.get_ad_group(user, ad_group_id)

        required_fields = ['start_date', 'end_date', 'account', 'campaign', 'ad_group', 'title', 'image_url', 'source']
        fieldnames = _get_fieldnames(required_fields, additional_fields, '')

        conversion_goals = []
        if user.has_perm('zemauth.conversion_reports'):
            conversion_goals = ad_group.campaign.conversiongoal_set.all()
            for conversion_goal in conversion_goals:
                if conversion_goal.get_view_key() in additional_fields:
                    fieldnames[conversion_goal.get_view_key()] = conversion_goal.name

        results = _generate_content_ad_rows(
            ['content_ad', 'source'],
            start_date,
            end_date,
            user,
            order,
            True,
            conversion_goals,
            ad_group=ad_group,
            source=filtered_sources)

        for row in results:
            row['start_date'] = start_date
            row['end_date'] = end_date
            row['account'] = ad_group.campaign.account.name
            row['campaign'] = ad_group.campaign.name
            row['ad_group'] = ad_group.name

        return get_csv_content(fieldnames, results, include_header=include_header)


class AdGroupAdsPlusExport(object):
    def get_data_current_view(self, user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields, include_header=True, include_archived=False):

        ad_group = helpers.get_ad_group(user, ad_group_id)

        required_fields = ['start_date', 'end_date', 'account', 'campaign', 'ad_group', 'title', 'image_url']
        fieldnames = _get_fieldnames(required_fields, additional_fields, '')

        conversion_goals = []
        if user.has_perm('zemauth.conversion_reports'):
            conversion_goals = ad_group.campaign.conversiongoal_set.all()
            for conversion_goal in conversion_goals:
                if conversion_goal.get_view_key() in additional_fields:
                    fieldnames[conversion_goal.get_view_key()] = conversion_goal.name

        results = _generate_content_ad_rows(
            ['content_ad'],
            start_date,
            end_date,
            user,
            order,
            True,
            conversion_goals,
            ad_group=ad_group,
            source=filtered_sources)
        
        for row in results:
            row['start_date'] = start_date
            row['end_date'] = end_date
            row['account'] = ad_group.campaign.account.name
            row['campaign'] = ad_group.campaign.name
            row['ad_group'] = ad_group.name

        return get_csv_content(fieldnames, results, include_header=include_header)

        '''
        ad_group = helpers.get_ad_group(user, ad_group_id)

        results = table.AdGroupAdsPlusTable().get(
            user,
            ad_group_id,
            filtered_sources,
            start_date,
            end_date,
            order,
            1,
            4294967295,
            include_archived,
            return_rows_only=True
        )

        required_fields = ['start_date', 'end_date', 'account', 'campaign', 'ad_group', 'name', 'image_urls']
        fieldnames = _get_fieldnames(required_fields, additional_fields, 'Title')
        for row in results:
            row['start_date'] = start_date
            row['end_date'] = end_date
            row['account'] = ad_group.campaign.account.name
            row['campaign'] = ad_group.campaign.name
            row['ad_group'] = ad_group.name
            content_ad = models.ContentAd.objects.get(id=row['id'])
            row['name'] = content_ad.title
            row['urlLink'] = content_ad.url
            row['image_urls'] = content_ad.get_image_url()

        if user.has_perm('zemauth.conversion_reports'):
            for conversion_goal in ad_group.campaign.conversiongoal_set.all():
                if conversion_goal.get_view_key() in additional_fields:
                    fieldnames[conversion_goal.get_view_key()] = conversion_goal.name

        return get_csv_content(fieldnames, results, include_header=include_header)
        '''
