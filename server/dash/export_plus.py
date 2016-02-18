import unicodecsv
import StringIO
import slugify
import time
from decimal import Decimal
from collections import OrderedDict

from dash import models
from dash import stats_helper
from dash import budget
from dash import constants
from dash import bcm_helpers
from dash.views import helpers

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
    'cost': 'Media Spend',
    'media_cost': 'Actual Media Spend',
    'data_cost': 'Actual Data Spend',
    'e_data_cost': 'Data Cost',
    'e_media_cost': 'Media Spend',
    'billing_cost': 'Total Spend',
    'total_cost': 'Actual Total Spend',
    'cpc': 'Average CPC',
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
    'date': 'Date',
    'license_fee': 'License Fee',
    'total_fee': 'Total Fee',
    'flat_fee': 'Recognized Flat Fee',
    'spend_projection': 'Spend projection',
    'credit_projection': 'Total credit',
}

UNEXPORTABLE_FIELDS = ['last_sync', 'supply_dash_url', 'state',
                       'submission_status', 'titleLink', 'bid_cpc',
                       'min_bid_cpc', 'max_bid_cpc', 'current_bid_cpc',
                       'daily_budget', 'current_daily_budget', 'yesterday_cost',
                       'image_urls', 'urlLink', 'upload_time',
                       'batch_name', 'display_url', 'brand_name',
                       'description', 'call_to_action', 'e_yesterday_cost']

FORMAT_1_DECIMAL = ['avg_tos']

FORMAT_2_DECIMALS = ['pv_per_visit', 'avg_tos', 'cost', 'data_cost', 'media_cost',
                     'e_media_cost', 'e_data_cost',
                     'total_cost', 'billing_cost', 'budget', 'available_budget',
                     'unspent_budget', 'license_fee', 'total_fee', 'flat_fee', ]

FORMAT_3_DECIMALS = ['cpc']

FORMAT_DIVIDE_100 = ['percent_new_users', 'bounce_rate', 'ctr', 'click_discrepancy']

FORMAT_EMPTY_TO_0 = [
    'data_cost', 'cost', 'cpc',
    'clicks', 'impressions', 'ctr', 'visits', 'pageviews',
    'e_media_cost', 'media_cost', 'e_data_cost', 'total_cost',
    'billing_cost', 'license_fee', 'total_fee', 'flat_fee',
]


def _generate_rows(dimensions, start_date, end_date, user, ordering, ignore_diff_rows,
                   conversion_goals, include_budgets=False, include_flat_fees=False,
                   include_projections=False, **constraints):
    stats = stats_helper.get_stats_with_conversions(
        user,
        start_date,
        end_date,
        breakdown=dimensions,
        ignore_diff_rows=ignore_diff_rows,
        conversion_goals=conversion_goals,
        constraints=constraints
    )
    prefetched_data, budgets, projections, flat_fees, statuses = _prefetch_rows_data(
        dimensions,
        constraints,
        stats,
        start_date,
        end_date,
        include_budgets=include_budgets,
        include_flat_fees=include_flat_fees,
        include_projections=include_projections)

    if 'source' in dimensions:
        source_names = {source.id: source.name for source in models.Source.objects.all()}

    for stat in stats:
        stat['start_date'] = start_date
        stat['end_date'] = end_date

        if 'content_ad' in dimensions:
            stat = _populate_content_ad_stat(stat, prefetched_data[stat['content_ad']])
        elif 'ad_group' in dimensions:
            stat = _populate_ad_group_stat(stat, prefetched_data.get(id=stat['ad_group']), statuses=statuses)
        elif 'campaign' in dimensions:
            stat = _populate_campaign_stat(stat, prefetched_data.get(
                id=stat['campaign']), statuses=statuses, budgets=budgets)
        elif 'account' in dimensions:
            stat = _populate_account_stat(stat, prefetched_data, statuses,
                                          projections=projections,
                                          budgets=budgets, flat_fees=flat_fees)
        else:
            ad_group_sources = models.AdGroupSource.objects.filter(
                ad_group__campaign__account__in=models.Account.objects.all().filter_by_user(user),
                source=stat['source'])
            stat['status'] = stat['status'] = _get_sources_state(ad_group_sources)

        if 'source' in stat:
            stat['source'] = source_names[stat['source']]

        # Adjsut by day breakdown
        if 'date' in stat:
            _adjust_breakdown_by_day(start_date, stat)

    return sort_results(stats, [ordering])


def _adjust_breakdown_by_day(start_date, stat):
    if stat['date'] == start_date or stat['date'].day == 1:
        return
    for field in ('credit_projection', 'flat_fee', 'total_fee', 'spend_projection'):
        if field in stat:
            stat[field] = Decimal(0.0)


def _prefetch_rows_data(dimensions, constraints, stats, start_date, end_date,
                        include_budgets=False, include_flat_fees=False, include_projections=False):
    data = None
    budgets = None
    projections = None
    statuses = None
    flat_fees = None
    by_source = ('source' in dimensions)
    level = None
    if 'content_ad' in dimensions:
        data = _prefetch_content_ad_data(constraints)
    elif 'ad_group' in dimensions:
        level = 'ad_group'
        distinct_ad_groups = set(stat['ad_group'] for stat in stats)
        data = models.AdGroup.objects.select_related('campaign__account').filter(id__in=distinct_ad_groups)
    elif 'campaign' in dimensions:
        level = 'campaign'
        distinct_campaigns = set(stat['campaign'] for stat in stats)
        data = models.Campaign.objects.select_related('account').filter(id__in=distinct_campaigns)
    elif 'account' in dimensions:
        level = 'account'
        accounts = set(stat['account'] for stat in stats)
        data = models.Account.objects.filter(id__in=accounts)
        flat_fees = _prefetch_flat_fees(data, start_date, end_date)
        if include_projections:
            projections = bcm_helpers.get_projections(data, start_date, end_date)

    if level in ['account', 'campaign', 'ad_group']:
        statuses = _prefetch_statuses(data, level, by_source, constraints.get('source'))
        budgets = None if not include_budgets else _prefetch_budgets(data, level)
    return data, budgets, projections, flat_fees, statuses


def _prefetch_flat_fees(accounts, start_date, end_date):
    account_flat_fees = {}
    for credit in models.CreditLineItem.objects.filter(account__in=accounts):
        if not credit.flat_fee_cc:
            continue
        if credit.account_id not in account_flat_fees:
            account_flat_fees[credit.account_id] = Decimal('0.0')
        account_flat_fees[credit.account_id] += credit.get_flat_fee_on_date_range(start_date,
                                                                                  end_date)
    return account_flat_fees


def _prefetch_account_budgets(accounts):
    all_accounts_budget = budget.GlobalBudget().get_total_by_account()
    all_accounts_total_spend = budget.GlobalBudget().get_spend_by_account()
    result = {
        acc.id: {
            'budget': Decimal(all_accounts_budget.get(acc.id, 0)),
            'spent_budget': Decimal(all_accounts_total_spend.get(acc.id, 0))
        } for acc in accounts if not acc.uses_credits
    }
    accounts_budget, accounts_spend = bcm_helpers.get_account_media_budget_data(
        acc.pk for acc in accounts if acc.uses_credits
    )
    result.update({
        acc.pk: {
            'budget': Decimal(accounts_budget.get(acc.id, 0)),
            'spent_budget': Decimal(accounts_spend.get(acc.id, 0)),
        } for acc in accounts if acc.uses_credits
    })
    return result


def _prefetch_campaign_budgets(campaigns):
    if campaigns and campaigns[0].account.uses_credits:
        total_budget, spent_budget = bcm_helpers.get_campaign_media_budget_data(
            camp.pk for camp in campaigns
        )
        return {
            camp.id: {
                'budget': Decimal(total_budget.get(camp.id, 0)),
                'spent_budget': Decimal(spent_budget.get(camp.id, 0)),
            } for camp in campaigns
        }
    return {
        camp.id: {
            'budget': Decimal(budget.CampaignBudget(camp).get_total()),
            'spent_budget': Decimal(budget.CampaignBudget(camp).get_spend())
        } for camp in campaigns
    }


def _prefetch_budgets(data, level):
    result = None
    if level == 'account':
        result = _prefetch_account_budgets(data)
    elif level == 'campaign':
        result = _prefetch_campaign_budgets(data)
    return result


def _prefetch_statuses(entities, level, by_source, sources=None):
    if level == 'account':
        model_class = models.Account
        by_source_constraints = 'ad_group__campaign__account'
        constraints = 'campaign__account_id'
    elif level == 'campaign':
        model_class = models.Campaign
        by_source_constraints = 'ad_group__campaign'
        constraints = 'campaign_id'
    elif level == 'ad_group':
        model_class = models.AdGroup
        by_source_constraints = 'ad_group'
        constraints = 'id'

    if by_source:
        ad_group_sources = helpers.get_active_ad_group_sources(model_class, entities)
        return {entity.id: {ad_group_source.source.id:
                            _get_sources_state(ad_group_sources.filter(
                                source=ad_group_source.source.id, **{by_source_constraints: entity}))
                            for ad_group_source in ad_group_sources.filter(**{by_source_constraints: entity})}
                for entity in entities}

    ad_groups = models.AdGroup.objects.filter(**{constraints + '__in': entities})
    ad_groups_settings = models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups).group_current_settings()

    ad_group_sources_settings = models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group__in=ad_groups).filter_by_sources(sources).group_current_settings()

    return helpers.get_ad_group_state_by_sources_running_status(
        ad_groups, ad_groups_settings, ad_group_sources_settings, constraints)


def _populate_content_ad_stat(stat, content_ad):
    stat['ad_group'] = content_ad.ad_group.name
    stat['campaign'] = content_ad.ad_group.campaign.name
    stat['account'] = content_ad.ad_group.campaign.account.name
    stat['title'] = content_ad.title
    stat['url'] = content_ad.url
    stat['image_url'] = content_ad.get_image_url()
    stat['uploaded'] = content_ad.created_dt.date()
    stat['status'] = content_ad.state
    return stat


def _populate_ad_group_stat(stat, ad_group, statuses):
    stat['campaign'] = ad_group.campaign.name
    stat['account'] = ad_group.campaign.account.name
    stat['status'] = statuses[ad_group.id]
    if 'source' in stat:
        stat['status'] = stat['status'].get(stat['source'])
    stat['ad_group'] = ad_group.name
    return stat


def _populate_campaign_stat(stat, campaign, statuses, budgets=None):
    stat['campaign'] = campaign
    stat['account'] = campaign.account.name
    if budgets:
        stat['budget'] = budgets[campaign.id].get('budget')
        stat['available_budget'] = stat['budget'] - budgets[campaign.id].get('spent_budget')
        stat['unspent_budget'] = stat['budget'] - Decimal(stat.get('cost') or 0)
    stat['status'] = statuses[campaign.id]
    if 'source' in stat:
        stat['status'] = stat['status'].get(stat['source'])
    return stat


def _populate_account_stat(stat, prefetched_data, statuses, projections=None,
                           budgets=None, flat_fees=None):
    if budgets:
        stat['budget'] = budgets[stat['account']].get('budget')
        stat['available_budget'] = stat['budget'] - budgets[stat['account']].get('spent_budget')
        stat['unspent_budget'] = stat['budget'] - Decimal(stat.get('cost') or 0)
    if flat_fees is not None:
        stat['flat_fee'] = flat_fees.get(stat['account'], Decimal('0.0'))
        stat['total_fee'] = stat['flat_fee'] + Decimal(stat.get('license_fee') or 0)
    if projections:
        stat['credit_projection'] = projections['credit_projection'].get(stat['account'],
                                                                         Decimal('0.0'))
        stat['spend_projection'] = projections['spend_projection'].get(stat['account'],
                                                                       Decimal('0.0'))

    stat['status'] = statuses[stat['account']]
    if 'source' in stat:
        stat['status'] = stat['status'].get(stat['source'])
    stat['account'] = prefetched_data.get(id=stat['account']).name
    return stat


def _get_sources_state(ad_group_sources):
    if any(s.state == constants.AdGroupSourceSettingsState.ACTIVE
            for s in helpers.get_ad_group_sources_states(ad_group_sources)):
        return constants.ExportPlusStatus.ACTIVE
    return constants.ExportPlusStatus.INACTIVE


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


def _adjust_ordering(order, dimensions):
    trailing_dash = ('-' if order[0] == '-' else '')
    if 'date' in dimensions:
        return 'date'
    elif order in ['state', 'status_setting', '-state', '-status_setting']:
        return trailing_dash + 'status'
    elif order in ['name', '-name']:
        if 'source' in dimensions:
            return trailing_dash + 'source'
        elif 'ad_group' in dimensions:
            return trailing_dash + 'ad_group'
        elif 'campaign' in dimensions:
            return trailing_dash + 'campaign'
        elif 'account' in dimensions:
            return trailing_dash + 'account'
    return order


def get_csv_content(fieldnames, data):
    output = StringIO.StringIO()
    writer = unicodecsv.DictWriter(output, fieldnames, encoding='utf-8', dialect='excel')
    writer.writerow(fieldnames)
    for item in data:
        # Format
        row = {}
        for field in fieldnames.keys():
            value = item.get(field)
            formatted_value = value

            if not value and field in FORMAT_EMPTY_TO_0:
                formatted_value = 0
                value = 0
            elif not value and field not in FORMAT_EMPTY_TO_0:
                formatted_value = ''
            elif field in FORMAT_DIVIDE_100:
                value = '{:.4f}'.format(value / 100)

            formatted_value = _format_decimals(value, field)
            formatted_value = _format_statuses_and_dates(formatted_value, field)

            if ';' in repr(formatted_value):
                formatted_value = '"' + formatted_value + '"'

            row[field] = formatted_value

        writer.writerow(row)

    return output.getvalue()


def _format_statuses_and_dates(value, field):
    if field == 'date':
        return value.strftime('%Y-%m-%d')
    elif field == 'status':
        return constants.ExportPlusStatus.get_text(value)
    return value


def _format_decimals(value, field):
    if value and field in FORMAT_1_DECIMAL:
        return '{:.1f}'.format(value)
    elif value and field in FORMAT_2_DECIMALS:
        return '{:.2f}'.format(value)
    elif value and field in FORMAT_3_DECIMALS:
        return '{:.3f}'.format(value)
    return value


def _get_fieldnames(required_fields, additional_fields, exclude=[]):
    fieldname_pairs = FIELDNAMES
    fieldname_pairs['status'] = 'Status (' + time.strftime('%Y-%m-%d') + ')'
    fields = [field for field in (required_fields + additional_fields) if field not in (UNEXPORTABLE_FIELDS + exclude)]
    fieldnames = OrderedDict([(k, fieldname_pairs.get(k) or k) for k in fields])
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

    def get_data(self, user, filtered_sources, start_date, end_date, order,
                 additional_fields, breakdown=None, by_source=False, by_day=False):
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
        required_fields.extend(['status'])

        include_budgets = (
            any([
                field in additional_fields
                for field in ['budget', 'available_budget', 'unspent_budget']
            ]) and not by_day and breakdown != 'ad_group'
        )
        include_flat_fees = (
            'total_fee' in additional_fields or 'flat_fee' in additional_fields
        )
        include_projections = (
            'spend_projection' in additional_fields or 'credit_projection' in additional_fields
        )

        if not include_budgets:
            exclude_fields.extend(['budget', 'available_budget', 'unspent_budget'])

        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)
        order = _adjust_ordering(order, dimensions)
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
            include_flat_fees=include_flat_fees,
            include_projections=include_projections,
            account=accounts,
            source=filtered_sources)

        return get_csv_content(fieldnames, results)


class AccountExport(object):

    def get_data(self, user, account_id, filtered_sources, start_date, end_date,
                 order, additional_fields, breakdown=None, by_source=False, by_day=False):
        account = helpers.get_account(user, account_id)

        dimensions = ['account']
        required_fields = ['start_date', 'end_date', 'account']
        exclude_fields = []
        exclude_budgets = False
        if breakdown == 'campaign':
            required_fields.extend(['campaign'])
            dimensions.extend(['campaign'])
        elif breakdown == 'ad_group':
            required_fields.extend(['campaign', 'ad_group'])
            dimensions.extend(['campaign', 'ad_group'])
            exclude_budgets = True
        elif breakdown == 'content_ad':
            required_fields.extend(['campaign', 'ad_group', 'title', 'image_url', 'url'])
            dimensions.extend(['campaign', 'ad_group', 'content_ad'])
            exclude_budgets = True
        if exclude_budgets or by_day:
            exclude_fields.extend(['budget', 'available_budget', 'unspent_budget'])
        required_fields.extend(['status'])

        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)
        order = _adjust_ordering(order, dimensions)
        fieldnames = _get_fieldnames(required_fields, additional_fields, exclude=exclude_fields)
        include_budgets = any(
            [field in fieldnames for field in ['budget', 'available_budget', 'unspent_budget']]) and not by_day

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

    def get_data(self, user, campaign_id, filtered_sources, start_date, end_date,
                 order, additional_fields, breakdown=None, by_source=False, by_day=False):
        campaign = helpers.get_campaign(user, campaign_id)

        dimensions = ['campaign']
        required_fields = ['start_date', 'end_date', 'account', 'campaign']

        if breakdown == 'ad_group':
            required_fields.extend(['ad_group'])
            dimensions.extend(['ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['ad_group', 'title', 'image_url', 'url'])
            dimensions.extend(['ad_group', 'content_ad'])
        required_fields.extend(['status'])
        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)
        order = _adjust_ordering(order, dimensions)
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

    def get_data(self, user, ad_group_id, filtered_sources, start_date, end_date,
                 order, additional_fields, breakdown=None, by_source=False, by_day=False):

        ad_group = helpers.get_ad_group(user, ad_group_id)

        required_fields = ['start_date', 'end_date', 'account', 'campaign', 'ad_group']
        dimensions = []

        if breakdown == 'ad_group':
            dimensions.extend(['ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['title', 'image_url', 'url'])
            dimensions.extend(['content_ad'])
        required_fields.extend(['status'])
        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)
        order = _adjust_ordering(order, dimensions)
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


def filter_allowed_fields(request, fields):
    allowed_fields = []
    can_view_effective_costs = request.user.has_perm('zemauth.can_view_effective_costs')
    can_view_actual_costs = request.user.has_perm('zemauth.can_view_actual_costs')
    can_view_flat_fees = request.user.has_perm('zemauth.can_view_flat_fees')
    can_see_projections = request.user.has_perm('zemauth.can_see_projections')
    for f in fields:
        if f in ('e_data_cost', 'e_media_cost',
                 'license_fee', 'billing_cost') and not can_view_effective_costs:
            continue
        if f in ('data_cost', 'media_cost',
                 'license_fee', 'total_cost') and not can_view_actual_costs:
            continue
        if f in ('cost', ) and (can_view_effective_costs or can_view_actual_costs):
            continue
        if f in ('total_fee', 'flat_fee', ) and not can_view_flat_fees:
            continue
        if f in ('credit_projection', 'spend_projection') and not can_see_projections:
            continue
        allowed_fields.append(f)
    return allowed_fields


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
    additional_fields = filter_allowed_fields(
        request,
        helpers.get_additional_columns(request.GET.get('additional_fields'))
    )

    granularity = get_granularity_from_type(request.GET.get('type'))

    return _get_report(
        request.user,
        helpers.get_stats_start_date(request.GET.get('start_date')),
        helpers.get_stats_end_date(request.GET.get('end_date')),
        filtered_sources=helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources')),
        order=request.GET.get('order') or 'name',
        additional_fields=additional_fields,
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
        filtered_sources=None,
        order=None,
        additional_fields=None,
        granularity=None,
        breakdown=None,
        by_day=False,
        by_source=False,
        ad_group=None,
        campaign=None,
        account=None):

    if not user.has_perm('zemauth.exports_plus'):
        raise exc.ForbiddenError(message='Not allowed')

    if not filtered_sources:
        filtered_sources = []

    if not additional_fields:
        additional_fields = []

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


def _get_report_contents(user, filtered_sources, start_date, end_date, order, additional_fields,
                         breakdown, by_source, by_day, account_id=None, campaign_id=None, ad_group_id=None):
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


def _get_report_filename(granularity, start_date, end_date, account_name='', campaign_name='',
                         ad_group_name='', by_source=False, by_day=False):
    name = ''
    all_accounts_name = ''
    if granularity == constants.ScheduledReportGranularity.ALL_ACCOUNTS or not any(
            [account_name, campaign_name, ad_group_name]):
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
