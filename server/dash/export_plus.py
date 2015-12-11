import unicodecsv
import StringIO
import slugify
from collections import OrderedDict

from dash import models
from dash import stats_helper
from dash import budget
from dash import constants
from dash.views import helpers
import reports.api_contentads

from utils import exc

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
    'data_cost': 'Data Cost',
    'cpc': 'Average CPC',
    'ctr': 'CTR',
    'ctr': 'CTR',
    'url': 'URL',
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
    'visits': 'Visits',
    'date': 'Date'
}

UNEXPORTABLE_FIELDS = ['last_sync', 'supply_dash_url', 'state',
                       'submission_status', 'titleLink', 'bid_cpc',
                       'min_bid_cpc', 'max_bid_cpc', 'current_bid_cpc',
                       'daily_budget', 'current_daily_budget', 'yesterday_cost',
                       'image_urls', 'urlLink', 'upload_time',
                       'batch_name', 'display_url', 'brand_name',
                       'description', 'call_to_action']

FORMAT_1_DECIMAL = ['avg_tos']

FORMAT_2_DECIMALS = ['ctr', 'click_discrepancy', 'percent_new_users', 'bounce_rate', 'pv_per_visit',
                     'avg_tos', 'cost', 'data_cost', 'budget', 'available_budget', 'unspent_budget']

FORMAT_3_DECIMALS = ['cpc']

FORMAT_DIVIDE_100 = ['percent_new_users', 'bounce_rate']


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

    if 'content_ad' in dimensions:
        content_ad_data = _prefetch_content_ad_data(constraints)

    if include_budgets and 'account' in dimensions:
        all_accounts_budget = budget.GlobalBudget().get_total_by_account()
        all_accounts_total_spend = budget.GlobalBudget().get_spend_by_account()

    if 'source' in dimensions:
        source_names = {source.id: source.name for source in models.Source.objects.all()}

    for stat in stats:
        stat['start_date'] = start_date
        stat['end_date'] = end_date

        if 'source' in stat:
            stat['source'] = source_names[stat['source']]

        if 'content_ad' in dimensions:
            stat = _populate_content_ad_stat(stat, content_ad_data[stat['content_ad']])
        elif 'ad_group' in dimensions:
            stat = _populate_ad_group_stat(stat, stat['ad_group'])
        elif 'campaign' in dimensions:
            stat = _populate_campaign_stat(stat, stat['campaign'], include_budgets)
        elif 'account' in dimensions:
            if include_budgets:
                stat['budget'] = all_accounts_budget.get(stat['account'], 0)
                stat['available_budget'] = stat['budget'] - all_accounts_total_spend.get(stat['account'], 0)
                stat['unspent_budget'] = stat['budget'] - (stat.get('cost') or 0)
            stat['account'] = models.Account.objects.get(id=stat['account'])

    if 'date' in dimensions:
        ordering = 'date'
    else:
        ordering = _adjust_ordering_by_name(ordering, dimensions)

    return sort_results(stats, [ordering])


def _populate_content_ad_stat(stat, content_ad):
    stat['ad_group'] = content_ad.ad_group.name
    stat['campaign'] = content_ad.ad_group.campaign.name
    stat['account'] = content_ad.ad_group.campaign.account.name
    stat['title'] = content_ad.title
    stat['url'] = content_ad.url
    stat['image_url'] = content_ad.get_image_url()
    stat['uploaded'] = content_ad.created_dt.date()
    return stat


def _populate_ad_group_stat(stat, ad_group_id):
    ad_group = models.AdGroup.objects.select_related('campaign__account').get(id=ad_group_id)
    stat['ad_group'] = ad_group.name
    stat['campaign'] = ad_group.campaign.name
    stat['account'] = ad_group.campaign.account.name
    return stat


def _populate_campaign_stat(stat, campaign_id, include_budgets):
    campaign = models.Campaign.objects.select_related('account').get(id=campaign_id)
    stat['campaign'] = campaign
    stat['account'] = campaign.account.name
    if include_budgets:
        stat['budget'] = budget.CampaignBudget(campaign).get_total()
        stat['available_budget'] = stat['budget'] - budget.CampaignBudget(campaign).get_spend()
        stat['unspent_budget'] = stat['budget'] - (stat.get('cost') or 0)
    return stat


def _prefetch_content_ad_data(constraints):
    sources = None
    fields = {}
    for key in constraints:
        if key == 'source':
            sources = constraints[key]
        elif key == 'ad_group':
            fields['ad_group'] = constraints[key]
        elif key == 'campaign':
            fields['ad_group__campaign'] = constraints[key]
        elif key == 'account':
            fields['ad_group__campaign__account'] = constraints[key]
        else:
            fields[key] = constraints[key]
    content_ads = models.ContentAd.objects.filter(**fields).select_related('ad_group__campaign__account')
    if sources is not None:
        content_ads = content_ads.filter_by_sources(sources)
    return {c.id: c for c in content_ads}


def _adjust_ordering_by_name(order, dimensions):
    if order in ['name', '-name']:
        if 'source' in dimensions:
            return ('-' if order[0] == '-' else '') + 'source'
        elif 'ad_group' in dimensions:
            return ('-' if order[0] == '-' else '') + 'ad_group'
        elif 'campaign' in dimensions:
            return ('-' if order[0] == '-' else '') + 'campaign'
        elif 'account' in dimensions:
            return ('-' if order[0] == '-' else '') + 'account'
    return order


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
            formatted_value = value

            if not value:
                formatted_value = ''
            elif key in FORMAT_DIVIDE_100:
                value = value / 100

            if value and key in FORMAT_1_DECIMAL:
                formatted_value = '{:.1f}'.format(value)
            elif value and key in FORMAT_2_DECIMALS:
                formatted_value = '{:.2f}'.format(value)
            elif value and key in FORMAT_3_DECIMALS:
                formatted_value = '{:.3f}'.format(value)

            if key == 'date':
                formatted_value = value.strftime('%Y-%m-%d')

            if ';' in repr(formatted_value):
                formatted_value = '"' + formatted_value + '"'

            row[key] = formatted_value

        writer.writerow(row)

    return output.getvalue()


def _get_fieldnames(required_fields, additional_fields, exclude=[]):
    fields = [field for field in (required_fields + additional_fields) if field not in (UNEXPORTABLE_FIELDS + exclude)]
    fieldnames = OrderedDict([(k, FIELDNAMES.get(k) or k) for k in fields])
    return fieldnames


def _get_conversion_goals(user, campaign):
    if user.has_perm('zemauth.conversion_reports'):
        return campaign.conversiongoal_set.all()
    return []


def get_granularity_from_type(export_type):
    return {
        'allaccounts-csv': constants.ScheduledReportGranularity.ALL_ACCOUNTS,
        'account-csv': constants.ScheduledReportGranularity.ACCOUNT,
        'campaign-csv': constants.ScheduledReportGranularity.CAMPAIGN,
        'adgroup-csv': constants.ScheduledReportGranularity.AD_GROUP,
        'contentad-csv': constants.ScheduledReportGranularity.CONTENT_AD
    }.get(export_type)


def get_breakdown_from_granularity(granularity):
    return {
        constants.ScheduledReportGranularity.ALL_ACCOUNTS: None,
        constants.ScheduledReportGranularity.ACCOUNT: 'account',
        constants.ScheduledReportGranularity.CAMPAIGN: 'campaign',
        constants.ScheduledReportGranularity.AD_GROUP: 'ad_group',
        constants.ScheduledReportGranularity.CONTENT_AD: 'content_ad'
    }.get(granularity)


def _include_breakdowns(required_fields, dimensions, by_day, by_source):
    if by_source:
        required_fields.append('source')
        dimensions.append('source')
    if by_day:
        required_fields.append('date')
        dimensions.append('date')
    return required_fields, dimensions


class AllAccountsExport(object):
    def get_data(self, user, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None, by_source=False, by_day=False):
        accounts = models.Account.objects.all().filter_by_user(user).filter_by_sources(filtered_sources)
        if not user.has_perm('zemauth.view_archived_entities'):
            accounts = accounts.exclude_archived()

        required_fields = ['start_date', 'end_date']
        dimensions = []
        exclude_fields = []
        if breakdown == 'account':
            required_fields.extend(['account'])
            dimensions.extend(['account'])
        elif breakdown == 'campaign':
            required_fields.extend(['account', 'campaign'])
            dimensions.extend(['account', 'campaign'])
        elif breakdown == 'ad_group':
            required_fields.extend(['account', 'campaign', 'ad_group'])
            dimensions.extend(['account', 'campaign', 'ad_group'])

        include_budgets = (any([field in additional_fields for field in ['budget', 'available_budget', 'unspent_budget']])
                           and not by_day and breakdown != 'ad_group')
        if not include_budgets:
            exclude_fields.extend(['budget', 'available_budget', 'unspent_budget'])

        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)

        fieldnames = _get_fieldnames(required_fields, additional_fields, exclude=exclude_fields)

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


class AccountExport(object):
    def get_data(self, user, account_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None, by_source=False, by_day=False):
        account = helpers.get_account(user, account_id)

        dimensions = ['account']
        required_fields = ['start_date', 'end_date', 'account']
        exclude_fields = []

        if breakdown == 'campaign':
            required_fields.extend(['campaign'])
            dimensions.extend(['campaign'])
        elif breakdown == 'ad_group':
            required_fields.extend(['campaign', 'ad_group'])
            exclude_fields.extend(['budget', 'available_budget', 'unspent_budget'])
            dimensions.extend(['campaign', 'ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['campaign', 'ad_group', 'title', 'image_url', 'url'])
            exclude_fields.extend(['budget', 'available_budget', 'unspent_budget'])
            dimensions.extend(['campaign', 'ad_group', 'content_ad'])

        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)

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


class CampaignExport(object):
    def get_data(self, user, campaign_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None, by_source=False, by_day=False):
        campaign = helpers.get_campaign(user, campaign_id)

        dimensions = ['campaign']
        required_fields = ['start_date', 'end_date', 'account', 'campaign']

        if breakdown == 'ad_group':
            required_fields.extend(['ad_group'])
            dimensions.extend(['ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['ad_group', 'title', 'image_url', 'url'])
            dimensions.extend(['ad_group', 'content_ad'])

        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)

        fieldnames = _get_fieldnames(required_fields, additional_fields)

        conversion_goals = _get_conversion_goals(user, campaign)
        for conversion_goal in conversion_goals:
            if conversion_goal.get_view_key(conversion_goals) in additional_fields:
                fieldnames[conversion_goal.get_view_key(conversion_goals)] = conversion_goal.name

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


class AdGroupExport(object):
    def get_data(self, user, ad_group_id, filtered_sources, start_date, end_date, order, additional_fields, breakdown=None, by_source=False, by_day=False):

        ad_group = helpers.get_ad_group(user, ad_group_id)

        required_fields = ['start_date', 'end_date', 'account', 'campaign', 'ad_group']
        dimensions = []

        if breakdown == 'ad_group':
            dimensions.extend(['ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['title', 'image_url', 'url'])
            dimensions.extend(['content_ad'])

        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)

        fieldnames = _get_fieldnames(required_fields, additional_fields)

        conversion_goals = _get_conversion_goals(user, ad_group.campaign)
        for conversion_goal in conversion_goals:
            if conversion_goal.get_view_key(conversion_goals) in additional_fields:
                fieldnames[conversion_goal.get_view_key(conversion_goals)] = conversion_goal.name

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


def get_report_from_export_report(export_report, start_date, end_date):
    return _get_report(
        export_report.created_by,
        start_date,
        end_date,
        filtered_sources=export_report.get_filtered_sources(),
        order=export_report.order_by,
        additional_fields=export_report.get_additional_fields(),
        granularity=export_report.granularity,
        breakdown=get_breakdown_from_granularity(export_report.granularity),
        by_source=export_report.breakdown_by_source,
        by_day=export_report.breakdown_by_day,
        ad_group=export_report.ad_group,
        campaign=export_report.campaign,
        account=export_report.account
    )


def get_report_from_request(request, account=None, campaign=None, ad_group=None, by_source=False):
    granularity = get_granularity_from_type(request.GET.get('type'))
    return _get_report(
        request.user,
        helpers.get_stats_start_date(request.GET.get('start_date')),
        helpers.get_stats_end_date(request.GET.get('end_date')),
        filtered_sources=helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources')),
        order=request.GET.get('order') or 'name',
        additional_fields=helpers.get_additional_columns(request.GET.get('additional_fields')),
        granularity=granularity,
        breakdown=get_breakdown_from_granularity(granularity),
        by_source=by_source,
        by_day=helpers.get_by_day(request.GET.get('by_day')),
        ad_group=ad_group,
        campaign=campaign,
        account=account
    )


def _get_report(
        user,
        start_date,
        end_date,
        filtered_sources=[],
        order=None,
        additional_fields=[],
        granularity=None,
        breakdown=None,
        by_day=False,
        by_source=False,
        ad_group=None,
        campaign=None,
        account=None):
    if not user.has_perm('zemauth.exports_plus'):
        raise exc.ForbiddenError(message='Not allowed')
    account_name = campaign_name = ad_group_name = None
    account_id = campaign_id = ad_group_id = None
    if account:
        account_name = slugify.slugify(account.name)
        account_id = account.id
    elif campaign:
        account_name = slugify.slugify(campaign.account.name)
        campaign_name = slugify.slugify(campaign.name)
        campaign_id = campaign.id
    elif ad_group:
        account_name = slugify.slugify(ad_group.campaign.account.name)
        campaign_name = slugify.slugify(ad_group.campaign.name)
        ad_group_name = slugify.slugify(ad_group.name)
        ad_group_id = ad_group.id

    contents = _get_report_contents(
        user=user,
        filtered_sources=filtered_sources,
        start_date=start_date,
        end_date=end_date,
        order=order,
        additional_fields=additional_fields,
        breakdown=breakdown,
        by_source=by_source,
        by_day=by_day,
        account_id=account_id,
        campaign_id=campaign_id,
        ad_group_id=ad_group_id)

    filename = _get_report_filename(
        granularity=granularity,
        start_date=start_date,
        end_date=end_date,
        account_name=account_name,
        campaign_name=campaign_name,
        ad_group_name=ad_group_name,
        by_source=by_source,
        by_day=by_day
    )

    return (contents, filename)


def _get_report_contents(user, filtered_sources, start_date, end_date, order, additional_fields, breakdown, by_source, by_day, account_id=None, campaign_id=None, ad_group_id=None):
    arguments = {
        'user': user,
        'filtered_sources': filtered_sources,
        'start_date': start_date,
        'end_date': end_date,
        'order': order,
        'additional_fields': additional_fields,
        'breakdown': breakdown,
        'by_source': by_source,
        'by_day': by_day
    }

    if account_id:
        arguments['account_id'] = account_id
        return AccountExport().get_data(**arguments)
    elif campaign_id:
        arguments['campaign_id'] = campaign_id
        return CampaignExport().get_data(**arguments)
    elif ad_group_id:
        arguments['ad_group_id'] = ad_group_id
        return AdGroupExport().get_data(**arguments)
    return AllAccountsExport().get_data(**arguments)


def _get_report_filename(granularity, start_date, end_date, account_name='', campaign_name='', ad_group_name='', by_source=False, by_day=False):
    name = ''
    all_accounts_name = ''
    if granularity == constants.ScheduledReportGranularity.ALL_ACCOUNTS or not any([account_name, campaign_name, ad_group_name]):
        all_accounts_name = 'ZemantaOne'
    if granularity == constants.ScheduledReportGranularity.ACCOUNT and not account_name:
        name += '-_by_account'
    elif granularity == constants.ScheduledReportGranularity.CAMPAIGN and not campaign_name:
        name += '-_by_campaign'
    elif granularity == constants.ScheduledReportGranularity.AD_GROUP and not ad_group_name:
        name += '-_by_ad_group'
    elif granularity == constants.ScheduledReportGranularity.CONTENT_AD:
        name += '-_by_content_ad'

    return '_'.join(filter(None, (
        all_accounts_name,
        account_name,
        campaign_name,
        ad_group_name,
        name,
        ('media_source' if by_source else ''),
        ('by_day' if by_day else ''),
        'report',
        str(start_date),
        str(end_date))))
