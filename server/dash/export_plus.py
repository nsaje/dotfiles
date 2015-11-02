import unicodecsv
import StringIO
from collections import OrderedDict

from dash import models
from dash import stats_helper
from dash import budget
from dash.views import helpers
import reports.api_contentads

from utils.sort_helper import sort_results

FIELDNAMES = {
    'account': 'Account',
    'ad_group': 'Ad Group',
    'available_budget': 'Available Budget',
    'avg_tos': 'Avg. ToS',
    'bounce_rate': 'Bounce Rate',
    'budget': 'Total Budget',
    'campaign': 'Campaign',
    'click_discrepancy': 'Click Discrepancy',
    'clicks': 'Clicks',
    'cost': 'Spend',
    'cpc': 'Average CPC',
    'ctr': 'CTR',
    'ctr': 'CTR',
    'end_date': 'End Date',
    'image_url': 'Image URL',
    'impressions': 'Impressions',
    'pageviews': 'Pageviews',
    'percent_new_users': 'Percent New Users',
    'pv_per_visit': 'PV/Visit',
    'source': 'Source',
    'start_date': 'Start Date',
    'title': 'Title',
    'unspent_budget': 'Unspent Budget',
    'visits': 'Visits'
}

UNEXPORTABLE_FIELDS = ['last_sync', 'supply_dash_url', 'state',
                       'submission_status', 'titleLink', 'bid_cpc',
                       'min_bid_cpc', 'max_bid_cpc', 'current_bid_cpc',
                       'daily_budget', 'current_daily_budget', 'yesterday_cost',
                       'image_urls', 'urlLink', 'upload_time',
                       'batch_name', 'display_url', 'brand_name',
                       'description', 'call_to_action']


def _generate_rows(dimensions, start_date, end_date, user, ordering, ignore_diff_rows, conversion_goals, include_budgets=False, **constraints):
    stats = stats_helper.get_stats_with_conversions(
        user,
        start_date,
        end_date,
        breakdown=dimensions,
        ignore_diff_rows=ignore_diff_rows,
        conversion_goals=conversion_goals,
        constraints=constraints
    )

    if include_budgets and 'account' in dimensions:
        all_accounts_budget = budget.GlobalBudget().get_total_by_account()
        all_accounts_total_spend = budget.GlobalBudget().get_spend_by_account()

    for stat in stats:
        stat['start_date'] = start_date
        stat['end_date'] = end_date

        if 'source' in stat:
            stat['source'] = models.Source.objects.get(id=stat['source']).name
            if ordering in ['name', '-name']:
                ordering = ('-' if ordering[0] == '-' else '') + 'source'

        if 'content_ad' in dimensions:
            content_ad = models.ContentAd.objects.get(id=stat['content_ad'])
            stat['ad_group'] = content_ad.ad_group.name
            stat['campaign'] = content_ad.ad_group.campaign.name
            stat['account'] = content_ad.ad_group.campaign.account.name
            stat['title'] = content_ad.title
            stat['url'] = content_ad.url
            stat['image_url'] = content_ad.get_image_url()
            stat['uploaded'] = content_ad.created_dt.date()
        elif 'ad_group' in dimensions:
            ad_group = models.AdGroup.objects.get(id=stat['ad_group'])
            stat['ad_group'] = ad_group.name
            stat['campaign'] = ad_group.campaign.name
            stat['account'] = ad_group.campaign.account.name
            if ordering in ['name', '-name']:
                ordering = ('-' if ordering[0] == '-' else '') + 'ad_group'
        elif 'campaign' in dimensions:
            campaign = models.Campaign.objects.get(id=stat['campaign'])
            stat['campaign'] = campaign
            stat['account'] = campaign.account.name
            if ordering in ['name', '-name']:
                ordering = ('-' if ordering[0] == '-' else '') + 'campaign'
            if include_budgets:
                stat['budget'] = budget.CampaignBudget(campaign).get_total()
                stat['available_budget'] = stat['budget'] - budget.CampaignBudget(campaign).get_spend()
                stat['unspent_budget'] = stat['budget'] - (stat.get('cost') or 0)
        elif 'account' in dimensions:
            if include_budgets:
                stat['budget'] = all_accounts_budget.get(stat['account'], 0)
                stat['available_budget'] = stat['budget'] - all_accounts_total_spend.get(stat['account'], 0)
                stat['unspent_budget'] = stat['budget'] - (stat.get('cost') or 0)
            stat['account'] = models.Account.objects.get(id=stat['account'])
            if ordering in ['name', '-name']:
                ordering = ('-' if ordering[0] == '-' else '') + 'account'

        for goal in conversion_goals:
            stat[goal.name] = stat.pop(goal.get_view_key())

    return sort_results(stats, [ordering])


def get_csv_content(fieldnames, data, title_text=None):
    output = StringIO.StringIO()
    if title_text is not None:
        output.write('# {0}\n\n'.format(title_text))

    writer = unicodecsv.DictWriter(output, fieldnames, encoding='utf-8', dialect='excel')

    writer.writerow(fieldnames)

    for item in data:
        # Format
        row = {}
        for key in fieldnames.keys():
            value = item.get(key)

            if not value:
                value = '0'
            elif value and key in ['avg_tos']:
                value = '{:.1f}'.format(value)
            elif value and key in ['ctr', 'click_discrepancy', 'percent_new_users', 'bounce_rate', 'pv_per_visit',
                                   'avg_tos', 'cost', 'budget', 'available_budget', 'unspent_budget']:
                value = '{:.2f}'.format(value)
            elif value and key in ['cpc']:
                value = '{:.3f}'.format(value)

            row[key] = value
            if repr(value).find(';') != -1:
                row[key] = '"' + value + '"'

        writer.writerow(row)

    return output.getvalue()


def _get_fieldnames(required_fields, additional_fields, exclude=[]):
    fields = [field for field in (required_fields + additional_fields) if field not in (UNEXPORTABLE_FIELDS + exclude)]
    fieldnames = OrderedDict([(k, FIELDNAMES.get(k) or k) for k in fields])
    return fieldnames


class AllAccountsExport(object):
    def get_data(self, user, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None):
        accounts = models.Account.objects.all().filter_by_user(user).filter_by_sources(filtered_sources)
        if not user.has_perm('zemauth.view_archived_entities'):
            accounts = accounts.exclude_archived()

        required_fields = ['start_date', 'end_date', 'account']
        dimensions = ['account']
        exclude_fields = []

        if breakdown == 'campaign':
            required_fields.extend(['campaign'])
            dimensions.extend(['campaign'])
        elif breakdown == 'ad_group':
            required_fields.extend(['campaign', 'ad_group'])
            dimensions.extend(['campaign', 'ad_group'])
            exclude_fields.extend(['budget', 'available_budget', 'unspent_budget'])

        fieldnames = _get_fieldnames(required_fields, additional_fields, exclude=exclude_fields)
        include_budgets = any([field in fieldnames for field in ['budget', 'available_budget', 'unspent_budget']])

        results = _generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            order,
            False,
            [],
            include_budgets=include_budgets,
            account=accounts,
            source=filtered_sources)

        return get_csv_content(fieldnames, results)


class AccountCampaignsExport(object):
    def get_data(self, user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None):
        account = helpers.get_account(user, account_id)

        dimensions = ['campaign']
        required_fields = ['start_date', 'end_date', 'account', 'campaign']
        exclude_fields = []

        if breakdown == 'ad_group':
            required_fields.extend(['ad_group'])
            exclude_fields.extend(['budget', 'available_budget', 'unspent_budget'])
            dimensions.extend(['ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['ad_group', 'title', 'image_url'])
            exclude_fields.extend(['budget', 'available_budget', 'unspent_budget'])
            dimensions.extend(['ad_group', 'content_ad'])

        fieldnames = _get_fieldnames(required_fields, additional_fields, exclude=exclude_fields)
        include_budgets = any([field in fieldnames for field in ['budget', 'available_budget', 'unspent_budget']])

        results = _generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            order,
            breakdown == 'content_ad',
            [],
            include_budgets=include_budgets,
            account=account,
            source=filtered_sources)

        return get_csv_content(fieldnames, results)


class CampaignAdGroupsExport(object):
    def get_data(self, user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None):
        campaign = helpers.get_campaign(user, campaign_id)

        dimensions = ['ad_group']
        required_fields = ['start_date', 'end_date', 'account', 'campaign', 'ad_group']
        if breakdown == 'content_ad':
            required_fields.extend(['title', 'image_url'])
            dimensions.extend(['content_ad'])
        fieldnames = _get_fieldnames(required_fields, additional_fields)

        conversion_goals = []
        if user.has_perm('zemauth.conversion_reports'):
            conversion_goals = campaign.conversiongoal_set.all()
            for conversion_goal in conversion_goals:
                if conversion_goal.get_view_key() in additional_fields:
                    fieldnames[conversion_goal.get_view_key()] = conversion_goal.name

        results = _generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            order,
            breakdown == 'content_ad',
            conversion_goals,
            campaign=campaign,
            source=filtered_sources)

        return get_csv_content(fieldnames, results)


class SourcesExport(object):
    def get_data_all_accounts(self, user, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None):
        accounts = models.Account.objects.all().filter_by_user(user).filter_by_sources(filtered_sources)
        if not user.has_perm('zemauth.view_archived_entities'):
            accounts = accounts.exclude_archived()

        required_fields = ['start_date', 'end_date']
        dimensions = []

        if breakdown == 'account':
            required_fields.extend(['account'])
            dimensions.extend(['account'])
        elif breakdown == 'campaign':
            required_fields.extend(['account', 'campaign'])
            dimensions.extend(['account', 'campaign'])
        elif breakdown == 'ad_group':
            required_fields.extend(['account', 'campaign', 'ad_group'])
            dimensions.extend(['account', 'campaign', 'ad_group'])

        required_fields.extend(['source'])
        fieldnames = _get_fieldnames(required_fields, additional_fields)
        dimensions.extend(['source'])

        results = _generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            order,
            False,
            [],
            account=accounts,
            source=filtered_sources)

        return get_csv_content(fieldnames, results)

    def get_data_account(self, user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None):
        account = helpers.get_account(user, account_id)

        required_fields = ['start_date', 'end_date', 'account']
        dimensions = ['account']

        if breakdown == 'campaign':
            required_fields.extend(['campaign'])
            dimensions.extend(['campaign'])
        elif breakdown == 'ad_group':
            required_fields.extend(['campaign', 'ad_group'])
            dimensions.extend(['campaign', 'ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['campaign', 'ad_group', 'title', 'image_url'])
            dimensions.extend(['campaign', 'ad_group', 'content_ad'])

        required_fields.extend(['source'])
        fieldnames = _get_fieldnames(required_fields, additional_fields)
        dimensions.extend(['source'])

        results = _generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            order,
            breakdown == 'content_ad',
            [],
            account=account,
            source=filtered_sources)
        return get_csv_content(fieldnames, results)

    def get_data_campaign(self, user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None):
        campaign = helpers.get_campaign(user, campaign_id)

        required_fields = ['start_date', 'end_date', 'account', 'campaign']
        dimensions = ['campaign']

        if breakdown == 'ad_group':
            required_fields.extend(['ad_group'])
            dimensions.extend(['ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['ad_group', 'title', 'image_url'])
            dimensions.extend(['ad_group', 'content_ad'])

        required_fields.extend(['source'])
        fieldnames = _get_fieldnames(required_fields, additional_fields)
        dimensions.extend(['source'])

        conversion_goals = []
        if user.has_perm('zemauth.conversion_reports'):
            conversion_goals = campaign.conversiongoal_set.all()
            for conversion_goal in conversion_goals:
                if conversion_goal.get_view_key() in additional_fields:
                    fieldnames[conversion_goal.get_view_key()] = conversion_goal.name

        results = _generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            order,
            breakdown == 'content_ad',
            conversion_goals,
            campaign=campaign,
            source=filtered_sources)
        return get_csv_content(fieldnames, results)

    def get_data_ad_group(self, user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None):
        ad_group = helpers.get_ad_group(user, ad_group_id)

        required_fields = ['start_date', 'end_date', 'account', 'campaign', 'ad_group']
        dimensions = ['ad_group']

        if breakdown == 'content_ad':
            required_fields.extend(['title', 'image_url'])
            dimensions.extend(['content_ad'])

        required_fields.extend(['source'])
        fieldnames = _get_fieldnames(required_fields, additional_fields)
        dimensions.extend(['source'])

        conversion_goals = []
        if user.has_perm('zemauth.conversion_reports'):
            conversion_goals = ad_group.campaign.conversiongoal_set.all()
            for conversion_goal in conversion_goals:
                if conversion_goal.get_view_key() in additional_fields:
                    fieldnames[conversion_goal.get_view_key()] = conversion_goal.name

        results = _generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            order,
            breakdown == 'content_ad',
            conversion_goals,
            ad_group=ad_group,
            source=filtered_sources)

        return get_csv_content(fieldnames, results)


class AdGroupAdsPlusExport(object):
    def get_data(self, user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields):

        ad_group = helpers.get_ad_group(user, ad_group_id)

        required_fields = ['start_date', 'end_date', 'account', 'campaign', 'ad_group', 'title', 'image_url']
        fieldnames = _get_fieldnames(required_fields, additional_fields)

        conversion_goals = []
        if user.has_perm('zemauth.conversion_reports'):
            conversion_goals = ad_group.campaign.conversiongoal_set.all()
            for conversion_goal in conversion_goals:
                if conversion_goal.get_view_key() in additional_fields:
                    fieldnames[conversion_goal.get_view_key()] = conversion_goal.name

        results = _generate_rows(
            ['content_ad'],
            start_date,
            end_date,
            user,
            order,
            True,
            conversion_goals,
            ad_group=ad_group,
            source=filtered_sources)

        return get_csv_content(fieldnames, results)
