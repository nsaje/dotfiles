import unicodecsv
import StringIO
import slugify
import time
from decimal import Decimal
from collections import OrderedDict, defaultdict

from dash import models
from dash import stats_helper
from dash import constants
from dash import bcm_helpers
from dash import campaign_goals
from dash.views import helpers
from reports.projections import BudgetProjections

from utils.sort_helper import sort_results

FIELDNAMES = {
    'account_id': 'Account Id',
    'campaign_id': 'Campaign Id',
    'ad_group_id': 'Ad Group Id',
    'content_ad_id': 'Content Ad Id',
    'account': 'Account',
    'account_type': 'Account Type',
    'agency': 'Agency',
    'agency_id': 'Agency Id',
    'ad_group': 'Ad Group',
    'avg_tos': 'Avg. ToS',
    'bounce_rate': 'Bounce Rate',
    'campaign': 'Campaign',
    'click_discrepancy': 'Click Discrepancy',
    'clicks': 'Clicks',
    'media_cost': 'Actual Media Spend',
    'data_cost': 'Actual Data Spend',
    'e_data_cost': 'Data Cost',
    'e_media_cost': 'Media Spend',
    'billing_cost': 'Total Spend',
    'cpc': 'Average CPC',
    'ctr': 'CTR',
    'url': 'URL',
    'end_date': 'End Date',
    'image_url': 'Image URL',
    'image_hash': 'Image Hash',
    'label': 'Label',
    'impressions': 'Impressions',
    'pageviews': 'Pageviews',
    'percent_new_users': 'Percent New Users',
    'pv_per_visit': 'Pageviews per Visit',
    'source': 'Source',
    'start_date': 'Start Date',
    'title': 'Title',
    'visits': 'Visits',
    'date': 'Date',
    'license_fee': 'License Fee',
    'total_fee': 'Total Fee',
    'margin': 'Margin',
    'agency_total': 'Total Spend + Margin',
    'flat_fee': 'Recognized Flat Fee',
    'default_account_manager': 'Account Manager',
    'default_sales_representative': 'Sales Representative',
    'campaign_manager': 'Campaign Manager',
    'allocated_budgets': 'Media Budgets',
    'spend_projection': 'Spend Projection',
    'pacing': 'Pacing',
    'license_fee_projection': 'License Fee Projection',
    'total_fee_projection': 'Total Fee Projection',
    'total_seconds': 'Total Seconds',
    'unbounced_visits': 'Unbounced Visitors',
    'total_pageviews': 'Total Pageviews',
    'avg_cost_per_minute': 'Avg. Cost per Minute',
    'avg_cost_per_pageview': 'Avg. Cost per Pageview',
    'avg_cost_per_visit': 'Avg. Cost per Visit',
    'avg_cost_per_non_bounced_visitor': 'Avg. Cost for Unbounced Visitor',
    'avg_cost_for_new_visitor': 'Avg. Cost for New Visitor',
}

FIELDNAMES_ID_MAPPING = [('account', 'account_id'),
                         ('campaign', 'campaign_id'),
                         ('ad_group', 'ad_group_id'),
                         # content ad is never a required field, but title is
                         ('title', 'content_ad_id'),
                         ('agency', 'agency_id'),
                         ]

UNEXPORTABLE_FIELDS = ['last_sync', 'supply_dash_url', 'state',
                       'submission_status', 'titleLink', 'bid_cpc',
                       'min_bid_cpc', 'max_bid_cpc', 'current_bid_cpc',
                       'daily_budget', 'current_daily_budget', 'yesterday_cost',
                       'image_urls', 'urlLink', 'upload_time',
                       'batch_name', 'display_url', 'brand_name',
                       'description', 'call_to_action', 'e_yesterday_cost']

FORMAT_1_DECIMAL = ['avg_tos']

FORMAT_2_DECIMALS = ['pv_per_visit', 'avg_tos', 'data_cost', 'media_cost',
                     'e_media_cost', 'e_data_cost',
                     'billing_cost', 'margin', 'agency_total',
                     'license_fee', 'total_fee', 'flat_fee',
                     'allocated_budgets', 'spend_projection',
                     'license_fee_projection', 'total_fee_projection']

FORMAT_3_DECIMALS = ['cpc']

FORMAT_DIVIDE_100 = ['percent_new_users', 'bounce_rate', 'ctr', 'click_discrepancy', 'pacing']

FORMAT_EMPTY_TO_0 = [
    'data_cost', 'cpc',
    'clicks', 'impressions', 'ctr', 'visits', 'pageviews',
    'e_media_cost', 'media_cost', 'e_data_cost',
    'billing_cost', 'license_fee', 'total_fee', 'flat_fee',
    'margin', 'agency_total',
]

FORMAT_HASH = ['image_hash']

ACCOUNT_ONLY_ONCE_FIELDS = ('flat_fee', 'total_fee',
                            'total_fee_projection')

ACCOUNT_CAMPAIGN_ONLY_ONCE_FIELDS = ACCOUNT_ONLY_ONCE_FIELDS + ('allocated_budgets',
                                                                'license_fee_projection',
                                                                'spend_projection', 'pacing')


def _generate_rows(dimensions, start_date, end_date, user, ordering, ignore_diff_rows,
                   conversion_goals, include_settings=False, include_account_settings=False, include_budgets=False,
                   include_flat_fees=False, include_projections=False, **constraints):
    stats = stats_helper.get_stats_with_conversions(
        user,
        start_date,
        end_date,
        breakdown=dimensions,
        ignore_diff_rows=ignore_diff_rows,
        conversion_goals=conversion_goals,
        constraints=constraints
    )
    prefetched_data, budgets, projections, account_projections, statuses, settings, account_settings =\
        _prefetch_rows_data(
            user,
            dimensions,
            constraints,
            stats,
            start_date,
            end_date,
            include_settings=include_settings,
            include_account_settings=include_account_settings,
            include_budgets=include_budgets,
            include_flat_fees=include_flat_fees,
            include_projections=include_projections,
        )

    if not dimensions:
        stats = [stats]

    source_names = None
    if 'source' in dimensions:
        source_names = {source.id: source.name for source in models.Source.objects.all()}

    account_appeared = defaultdict(bool)
    for stat in stats:
        _populate_stat(stat, start_date=start_date, end_date=end_date, dimensions=dimensions,
                       source_names=source_names, user=user, prefetched_data=prefetched_data,
                       budgets=budgets, projections=projections, account_projections=account_projections,
                       include_projections=include_projections, include_flat_fees=include_flat_fees,
                       statuses=statuses, settings=settings, account_settings=account_settings)

    campaign = _get_campaign(constraints)
    if user.has_perm('zemauth.campaign_goal_optimization') and campaign:
        stats = campaign_goals.create_goals(campaign, stats)

    sorted_ret = list(sort_results(stats, [ordering]))

    is_breakdown_by_day = 'date' in dimensions
    first_stat_date = is_breakdown_by_day and list(
        sorted(stat.get('date') for stat in sorted_ret)
    )[0]

    for stat in sorted_ret:
        if is_breakdown_by_day:
            _adjust_breakdown_by_day(first_stat_date, stat)
        else:
            _adjust_breakdown_by_account(stat, account_appeared)

    return sorted_ret


def _get_campaign(constraints):
    if 'ad_group' in constraints:
        return constraints['ad_group'].campaign
    if 'campaign' in constraints:
        return constraints['campaign']
    return None


def _prefetch_rows_data(user, dimensions, constraints, stats, start_date, end_date, include_settings=False,
                        include_account_settings=False, include_budgets=False, include_flat_fees=False,
                        include_projections=False, filtered_all_accounts=None):
    data = None
    budgets = None
    projections = None
    statuses = None
    by_source = ('source' in dimensions)
    level = _level_from_dimensions(dimensions)
    settings = None
    account_settings = None
    if 'content_ad' in dimensions:
        data = _prefetch_content_ad_data(constraints)
    elif 'ad_group' in dimensions:
        data, settings, account_settings = _prefetch_ad_group_data(
            stats, include_settings=include_settings,
            include_account_settings=include_account_settings
        )
    elif 'campaign' in dimensions:
        data, settings, account_settings = _prefetch_campaign_data(
            stats, include_settings=include_settings,
            include_account_settings=include_account_settings
        )
    elif 'account' in dimensions:
        data, settings = _prefetch_account_data(stats, include_settings=include_settings)
    elif not dimensions:
        accounts = models.Account.objects.all().filter_by_user(user)
        data = {a.id: a for a in accounts}

    if level in ['account', 'campaign', 'ad_group']:
        statuses = _prefetch_statuses(data, level, by_source, constraints.get('source'))

    if level in ['all_accounts', 'account', 'campaign', 'ad_group']:
        budgets = None if not include_budgets \
            else _prefetch_budgets(data, level)

    projections, account_projections = _prefetch_projections(start_date, end_date, stats, level, user)
    return data, budgets, projections, account_projections, statuses, settings, account_settings


def _prefetch_account_settings(stats):
    distinct_accounts = set(stat['account'] for stat in stats)
    account_settings_qs = models.AccountSettings.objects \
        .filter(account__in=distinct_accounts) \
        .group_current_settings()
    account_settings = {s.account_id: s for s in account_settings_qs}
    return account_settings


def _prefetch_account_budgets(accounts):
    accounts_budget, accounts_spend = bcm_helpers.get_account_media_budget_data(accounts.keys())
    return {
        acc.pk: {
            'budget': Decimal(accounts_budget.get(acc.id, 0)),
            'spent_budget': Decimal(accounts_spend.get(acc.id, 0)),
        } for acc in accounts.values()
    }


def _prefetch_campaign_budgets(campaigns):
    total_budget, spent_budget = bcm_helpers.get_campaign_media_budget_data(campaigns.keys())
    return {
        camp.id: {
            'budget': Decimal(total_budget.get(camp.id, 0)),
            'spent_budget': Decimal(spent_budget.get(camp.id, 0)),
        } for camp in campaigns.values()
    }


def _prefetch_budgets(data, level):
    result = None
    if level == 'all_accounts':
        account_budgets = _prefetch_account_budgets(data)
        result = {
            'budget': sum(b['budget'] for b in account_budgets.values()),
            'spent_budget': sum(b['spent_budget'] for b in account_budgets.values())
        }
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
                for entity in entities.itervalues()}

    ad_groups = models.AdGroup.objects.filter(**{constraints + '__in': entities})
    ad_groups_settings = models.AdGroupSettings.objects.filter(
        ad_group__in=ad_groups).group_current_settings()

    ad_group_sources_settings = models.AdGroupSourceSettings.objects.filter(
        ad_group_source__ad_group__in=ad_groups).filter_by_sources(sources)\
                                                .group_current_settings()\
                                                .select_related('ad_group_source')

    return helpers.get_ad_group_state_by_sources_running_status(
        ad_groups, ad_groups_settings, ad_group_sources_settings, constraints)


def _populate_stat(stat, start_date=None, end_date=None, dimensions=None, source_names=None,
                   user=None, prefetched_data=None, budgets=None, projections=None,
                   account_projections=None, include_flat_fees=False,
                   include_projections=False, statuses=None, settings=None,
                   account_settings=None, first_stat_date=None):

    stat['start_date'] = start_date
    stat['end_date'] = end_date

    if dimensions == ['source']:
        _populate_source_stat(stat, user=user, source_names=source_names)
    else:
        _populate_model_stat(stat, dimensions=dimensions, prefetched_data=prefetched_data,
                             projections=projections, account_projections=account_projections,
                             include_projections=include_projections,
                             include_flat_fees=include_flat_fees, statuses=statuses,
                             settings=settings, account_settings=account_settings)

    if 'source' in stat:
        stat['source'] = source_names[stat['source']]


def _adjust_breakdown_by_day(first_stat_date, stat):
    if _should_show_all_fields_on_date(stat['date'], first_stat_date):
        return
    for field in ACCOUNT_CAMPAIGN_ONLY_ONCE_FIELDS:
        if field in stat:
            stat[field] = Decimal(0.0)


def _adjust_breakdown_by_account(stat, account_appeared):
    if not account_appeared[stat['account']]:
        account_appeared[stat['account']] = True
        return

    for field in ACCOUNT_ONLY_ONCE_FIELDS:
        if field in stat:
            stat[field] = Decimal(0.0)


def _populate_source_stat(stat, user=None, source_names=None):
    ad_group_sources = models.AdGroupSource.objects.filter(
        ad_group__campaign__account__in=models.Account.objects.all().filter_by_user(user),
        source=stat['source'])
    stat['status'] = stat['status'] = _get_sources_state(ad_group_sources)


def _populate_model_stat(stat, dimensions=None, prefetched_data=None,
                         projections=None, account_projections=None,
                         include_flat_fees=False, include_projections=False,
                         statuses=None, settings=None, account_settings=None):
    model = None
    if 'content_ad' in dimensions:
        model = prefetched_data[stat['content_ad']]
        stat = _populate_content_ad_stat(stat, model)
    elif 'ad_group' in dimensions:
        model = prefetched_data[stat['ad_group']]
        stat = _populate_ad_group_stat(
            stat, model, statuses, settings=settings,
            account_settings=account_settings
        )
    elif 'campaign' in dimensions:
        model = prefetched_data[stat['campaign']]
        stat = _populate_campaign_stat(
            stat, model, statuses, settings=settings,
            account_settings=account_settings
        )
        stat = _populate_campaign_projections_fees(
            stat, model,
            include_flat_fees=include_flat_fees, include_projections=include_projections,
            projections=projections, account_projections=account_projections,
            account_settings=account_settings
        )
    elif 'account' in dimensions:
        model = prefetched_data[stat['account']]
        stat = _populate_account_stat(stat, model, statuses, settings=settings,
                                      projections=projections,
                                      include_projections=include_projections,
                                      include_flat_fees=include_flat_fees)
    elif not dimensions:
        stat = _populate_all_accounts_stat(stat, projections=projections,
                                           include_projections=include_projections,
                                           include_flat_fees=include_flat_fees)

    if model:
        _populate_model_ids(stat, model)


def _populate_content_ad_stat(stat, content_ad):
    stat['ad_group'] = content_ad.ad_group.name
    stat['campaign'] = content_ad.ad_group.campaign.name
    stat['account'] = content_ad.ad_group.campaign.account.name
    stat['title'] = content_ad.title
    stat['url'] = content_ad.url
    stat['image_url'] = content_ad.get_image_url()
    stat['image_hash'] = content_ad.image_hash
    stat['label'] = content_ad.label
    stat['uploaded'] = content_ad.created_dt.date()
    stat['status'] = content_ad.state
    stat['archived'] = content_ad.archived
    if content_ad.ad_group.campaign.account.agency is not None:
        stat['agency'] = content_ad.ad_group.campaign.account.agency.name
    return stat


def _populate_ad_group_stat(stat, ad_group, statuses, settings=None,
                            account_settings=None):
    stat['campaign'] = ad_group.campaign.name
    stat['account'] = ad_group.campaign.account.name
    if account_settings and ad_group.campaign.account.id in account_settings:
        account_setting = account_settings[ad_group.campaign.account.id]
        stat['account_type'] = constants.AccountType.get_text(account_setting.account_type)
    stat['status'] = statuses[ad_group.id]
    if 'source' in stat:
        stat['status'] = stat['status'].get(stat['source'])
    if settings and ad_group.id in settings:
        stat['archived'] = settings[ad_group.id].archived
    stat['ad_group'] = ad_group.name
    if ad_group.campaign.account.agency is not None:
        stat['agency'] = ad_group.campaign.account.agency.name
    return stat


def _populate_ad_group_projections_fees(stat, ad_group,
                                        include_projections=False,
                                        include_flat_fees=False,
                                        projections=None,
                                        account_projections=None):
    if include_flat_fees and account_projections is not None:
        stat['flat_fee'] = account_projections.row(ad_group.campaign.account.pk, 'flat_fee')
        stat['total_fee'] = account_projections.row(ad_group.campaign.account.pk, 'total_fee')
        if include_projections:
            stat['total_fee_projection'] = account_projections.row(ad_group.campaign.account.pk,
                                                                   'total_fee_projection')
    return stat


def _populate_campaign_stat(stat, campaign, statuses,
                            settings=None, account_settings=None):
    stat['campaign'] = campaign
    stat['account'] = campaign.account.name
    if account_settings and campaign.account.id in account_settings:
        account_setting = account_settings[campaign.account.id]
        stat['account_type'] = constants.AccountType.get_text(account_setting.account_type)
    if settings and campaign.id in settings:
        setting = settings[campaign.id]
        stat['campaign_manager'] = helpers.get_user_full_name_or_email(setting.campaign_manager, default_value=None)
        stat['archived'] = setting.archived
    stat['status'] = statuses[campaign.id]
    if 'source' in stat:
        stat['status'] = stat['status'].get(stat['source'])
    if campaign.account.agency is not None:
        stat['agency'] = campaign.account.agency.name
    return stat


def _populate_campaign_projections_fees(
        stat, campaign, include_flat_fees=False,
        include_projections=False,
        projections=None,
        account_projections=None,
        account_settings=None):
    if include_projections:
        stat['allocated_budgets'] = projections.row(campaign.pk, 'allocated_media_budget')
        stat['pacing'] = projections.row(campaign.pk, 'pacing')
        stat['spend_projection'] = projections.row(campaign.pk, 'media_spend_projection')
        stat['license_fee_projection'] = projections.row(campaign.pk,
                                                         'license_fee_projection')
    if include_flat_fees and account_projections is not None:
        stat['flat_fee'] = account_projections.row(campaign.account.pk, 'flat_fee')
        stat['total_fee'] = account_projections.row(campaign.account.pk, 'total_fee')
        if include_projections:
            stat['total_fee_projection'] = account_projections.row(campaign.account.pk, 'total_fee_projection')
    return stat


def _populate_account_stat(stat, account, statuses, settings=None, projections=None,
                           include_flat_fees=False, include_projections=False):
    if settings and account.id in settings:
        setting = settings[account.id]
        stat['default_account_manager'] = \
            helpers.get_user_full_name_or_email(setting.default_account_manager, default_value=None)
        stat['default_sales_representative'] = \
            helpers.get_user_full_name_or_email(setting.default_sales_representative, default_value=None)
        stat['account_type'] = constants.AccountType.get_text(setting.account_type)
        stat['archived'] = setting.archived
    if include_projections:
        stat['allocated_budgets'] = projections.row(account.pk, 'allocated_media_budget')
        stat['pacing'] = projections.row(account.pk, 'pacing')
        stat['spend_projection'] = projections.row(account.pk, 'media_spend_projection')
        stat['license_fee_projection'] = projections.row(account.pk, 'license_fee_projection')
    if include_flat_fees:
        stat['flat_fee'] = projections.row(account.pk, 'flat_fee')
        stat['total_fee'] = projections.row(account.pk, 'total_fee')
        if include_projections:
            stat['total_fee_projection'] = projections.row(account.pk, 'total_fee_projection')

    stat['status'] = statuses[stat['account']]
    if 'source' in stat:
        stat['status'] = stat['status'].get(stat['source'])
    stat['account'] = account.name
    # TODO: Optionally filter by permission
    if account.agency is not None:
        stat['agency'] = account.agency.name
    return stat


def _populate_all_accounts_stat(stat, projections=None, include_projections=False,
                                include_flat_fees=None):
    if include_projections:
        stat['allocated_budgets'] = projections.total('allocated_media_budget')
        stat['pacing'] = projections.total('pacing')
        stat['spend_projection'] = projections.total('media_spend_projection')
        stat['license_fee_projection'] = projections.total('license_fee_projection')
    if include_flat_fees:
        stat['flat_fee'] = projections.total('flat_fee')
        stat['total_fee'] = projections.total('total_fee')
        if include_projections:
            stat['total_fee_projection'] = projections.total('total_fee_projection')
    return stat


def _populate_model_ids(stat, model):
    # Add model and all it's parent ids to stat
    if isinstance(model, models.ContentAd):
        stat['content_ad_id'] = model.id
        model = model.ad_group
    if isinstance(model, models.AdGroup):
        stat['ad_group_id'] = model.id
        model = model.campaign
    if isinstance(model, models.Campaign):
        stat['campaign_id'] = model.id
        model = model.account
    if isinstance(model, models.Account):
        stat['account_id'] = model.id
        if model.agency is not None:
            stat['agency_id'] = model.agency.id


def _get_sources_state(ad_group_sources):
    if any(s.state == constants.AdGroupSourceSettingsState.ACTIVE
            for s in helpers.get_ad_group_sources_states(ad_group_sources)):
        return constants.ExportStatus.ACTIVE
    return constants.ExportStatus.INACTIVE


def _level_from_dimensions(dimensions):
    if 'content_ad' in dimensions:
        return None
    elif 'ad_group' in dimensions:
        return 'ad_group'
    elif 'campaign' in dimensions:
        return 'campaign'
    elif 'account' in dimensions:
        return 'account'
    elif not dimensions:
        return 'all_accounts'
    return None


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
    content_ads = models.ContentAd.objects.filter(**fields).select_related('ad_group__campaign__account__agency')
    if sources is not None:
        content_ads = content_ads.filter_by_sources(sources)
    return {c.id: c for c in content_ads}


def _prefetch_ad_group_data(stats, include_settings=False, include_account_settings=False):
    distinct_ad_groups = set(stat['ad_group'] for stat in stats)

    ad_group_qs = models.AdGroup.objects.select_related('campaign__account').filter(id__in=distinct_ad_groups)
    data = {ad_group.id: ad_group for ad_group in ad_group_qs}

    settings = None
    if include_settings:
        settings_qs = models.AdGroupSettings.objects \
            .filter(ad_group__in=distinct_ad_groups) \
            .group_current_settings()
        settings = {s.ad_group_id: s for s in settings_qs}

    account_settings = None
    if include_account_settings:
        account_settings = _prefetch_account_settings(stats)
    return data, settings, account_settings


def _prefetch_campaign_data(stats, include_settings=False, include_account_settings=False):
    distinct_campaigns = set(stat['campaign'] for stat in stats)

    campaign_qs = models.Campaign.objects.select_related('account').filter(id__in=distinct_campaigns)
    data = {c.id: c for c in campaign_qs}

    settings = None
    if include_settings:
        settings_qs = models.CampaignSettings.objects \
            .filter(campaign__in=distinct_campaigns) \
            .group_current_settings() \
            .select_related('campaign_manager')
        settings = {s.campaign_id: s for s in settings_qs}

    account_settings = None
    if include_account_settings:
        account_settings = _prefetch_account_settings(stats)
    return data, settings, account_settings


def _prefetch_account_data(stats, include_settings=False, include_account_settings=False):
    distinct_accounts = set(stat['account'] for stat in stats)
    include_settings = include_settings or include_account_settings

    accounts_qs = models.Account.objects.filter(id__in=distinct_accounts)
    data = {a.id: a for a in accounts_qs}

    settings = None
    if include_settings:
        settings_qs = models.AccountSettings.objects \
            .filter(account__in=distinct_accounts) \
            .group_current_settings() \
            .select_related('default_account_manager', 'default_sales_representative')
        settings = {s.account_id: s for s in settings_qs}

    return data, settings


def _prefetch_projections(start_date, end_date, stats, level, user):
    if level not in ['all_accounts', 'account', 'campaign', 'ad_group']:
        return None, None
    projections_accounts = []
    if level is None or level == 'all_accounts':
        projections_accounts = models.Account.objects.all().filter_by_user(user)
    else:
        projections_accounts = models.Account.objects.all().filter(
            pk__in=set(stat['account'] for stat in stats if stat.get('account'))
        )

    if level == 'ad_group':
        projections_level = 'campaign'
    elif level and level != 'all_accounts':
        projections_level = level
    else:
        projections_level = 'account'
    return BudgetProjections(
        start_date,
        end_date,
        projections_level,
        accounts=projections_accounts,
    ), BudgetProjections(
        start_date,
        end_date,
        'account',
        accounts=projections_accounts,
    )


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
    writer = unicodecsv.DictWriter(output, fieldnames, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)
    writer.writerow(fieldnames)
    for item in data:
        row = {}
        archived = item.get('archived', False)
        for field in fieldnames.keys():
            formatted_value = item.get(field)
            formatted_value = _format_empty_value(formatted_value, field)
            formatted_value = _format_percentages(formatted_value, field)
            formatted_value = _format_decimals(formatted_value, field)
            formatted_value = _format_hash(formatted_value, field)
            formatted_value = _format_statuses_and_dates(formatted_value, field, archived)
            row[field] = formatted_value

        writer.writerow(row)

    return output.getvalue()


def _format_empty_value(value, field):
    if not value and field in FORMAT_EMPTY_TO_0:
        return 0
    elif not value and field not in FORMAT_EMPTY_TO_0:
        return ''
    return value


def _format_percentages(value, field):
    if value and field in FORMAT_DIVIDE_100:
        return '{:.4f}'.format(value / 100)
    return value


def _format_statuses_and_dates(value, field, archived):
    if field == 'date':
        return value.strftime('%Y-%m-%d')
    elif field == 'status':
        if archived:
            value = constants.ExportStatus.ARCHIVED
        return constants.ExportStatus.get_text(value)
    return value


def _format_decimals(value, field):
    if value and field in FORMAT_1_DECIMAL:
        return '{:.1f}'.format(value)
    elif value and field in FORMAT_2_DECIMALS:
        return '{:.2f}'.format(value)
    elif value and field in FORMAT_3_DECIMALS:
        return '{:.3f}'.format(value)
    return value


def _format_hash(value, field):
    if value and field in FORMAT_HASH:
        return '#{}'.format(value)
    return value


def _get_fieldnames(required_fields, additional_fields, exclude=[]):
    fieldname_pairs = FIELDNAMES
    fieldname_pairs['status'] = 'Status (' + time.strftime('%Y-%m-%d') + ')'
    fields = [field for field in (required_fields + additional_fields) if field not in (UNEXPORTABLE_FIELDS + exclude)]
    fieldnames = OrderedDict([(k, fieldname_pairs.get(k) or k) for k in fields])
    return fieldnames


def _get_conversion_goals(user, campaign):
    return campaign.conversiongoal_set.all()


def _extend_fieldnames(fieldnames, conversion_goals, additional_fields):
    for conversion_goal in conversion_goals:
        view_key = conversion_goal.get_view_key(conversion_goals)
        cpa_view_key = 'avg_cost_per_' + view_key
        if view_key in additional_fields:
            fieldnames[conversion_goal.get_view_key(conversion_goals)] = conversion_goal.name
        if cpa_view_key in additional_fields:
            fieldnames[cpa_view_key] = 'Avg. CPA ({})'.format(conversion_goal.name)
    return fieldnames


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


def _include_model_ids(required_fields):
    for field, field_id in FIELDNAMES_ID_MAPPING:
        try:
            idx = required_fields.index(field)
            required_fields.insert(idx, field_id)
        except ValueError:
            pass
    return required_fields


class AllAccountsExport(object):

    def get_data(self, user, filtered_sources, start_date, end_date, order,
                 additional_fields, view_filter=None, breakdown=None, by_source=False, by_day=False, include_model_ids=False):
        accounts = models.Account.objects.all()\
            .filter_by_user(user)\
            .filter_by_sources(filtered_sources)
        if view_filter is not None:
            accounts = accounts\
                .filter_by_agencies(view_filter.filtered_agencies)\
                .filter_by_account_types(view_filter.filtered_account_types)

        required_fields = ['start_date', 'end_date']
        if user.has_perm('zemauth.can_view_account_agency_information'):
            required_fields.append('agency')
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

        if breakdown or by_source:
            required_fields.extend(['status'])
        if include_model_ids:
            required_fields = _include_model_ids(required_fields)

        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)
        order = _adjust_ordering(order, dimensions)

        supported_settings_fields = ['default_account_manager', 'default_sales_representative']
        include_account_settings = breakdown == 'account' and \
                                                any(field in additional_fields for field in supported_settings_fields)
        if not include_account_settings:
            exclude_fields.extend(supported_settings_fields)

        # Only include account type field in reports for the following breakdowns: account, campaign, ad group
        if breakdown and 'account_type' in additional_fields:
            include_account_settings = True
        else:
            exclude_fields.extend(['account_type'])

        include_settings = False
        if 'status' in required_fields:
            # Settings are needed to get archived status
            include_settings = True

        include_flat_fees = (
            'total_fee' in additional_fields or 'flat_fee' in additional_fields or
            'total_fee_projection' in additional_fields
        )
        include_projections = bool(set([
            'pacing', 'spend_projection', 'allocated_budgets', 'total_fee_projection',
            'license_fee_projection'
        ]) & set(additional_fields))

        fieldnames = _get_fieldnames(required_fields, additional_fields, exclude=exclude_fields)

        results = _generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            order,
            False,
            [],
            include_settings=include_settings,
            include_account_settings=include_account_settings,
            include_flat_fees=include_flat_fees,
            include_projections=include_projections,
            account=accounts,
            source=filtered_sources)

        return get_csv_content(fieldnames, results)


class AccountExport(object):

    def get_data(self, user, account_id, filtered_sources, start_date, end_date,
                 order, additional_fields, breakdown=None, by_source=False, by_day=False, include_model_ids=False):
        account = helpers.get_account(user, account_id)

        dimensions = ['account']
        required_fields = ['start_date', 'end_date', 'account']
        if user.has_perm('zemauth.can_view_account_agency_information'):
            required_fields.insert(2, 'agency')
        exclude_fields = []
        if breakdown == 'campaign':
            required_fields.extend(['campaign'])
            dimensions.extend(['campaign'])
        elif breakdown == 'ad_group':
            required_fields.extend(['campaign', 'ad_group'])
            dimensions.extend(['campaign', 'ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['campaign', 'ad_group', 'title', 'image_url', 'image_hash', 'label', 'url'])
            dimensions.extend(['campaign', 'ad_group', 'content_ad'])

        required_fields.extend(['status'])
        if include_model_ids:
            required_fields = _include_model_ids(required_fields)

        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)
        order = _adjust_ordering(order, dimensions)

        include_campaign_manager = breakdown == 'campaign' and 'campaign_manager' in additional_fields
        if not include_campaign_manager:
            exclude_fields.append('campaign_manager')

        fieldnames = _get_fieldnames(required_fields, additional_fields, exclude=exclude_fields)

        include_projections = bool(set([
            'pacing', 'spend_projection', 'allocated_budgets',
            'license_fee_projection'
        ]) & set(additional_fields))

        results = _generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            order,
            breakdown == 'content_ad',
            [],
            include_settings=True,
            include_projections=include_projections,
            account=account,
            source=filtered_sources)

        return get_csv_content(fieldnames, results)


class CampaignExport(object):

    def get_data(self, user, campaign_id, filtered_sources, start_date, end_date,
                 order, additional_fields, breakdown=None, by_source=False, by_day=False, include_model_ids=False):
        campaign = helpers.get_campaign(user, campaign_id)

        dimensions = ['campaign']
        required_fields = ['start_date', 'end_date', 'account', 'campaign']

        if user.has_perm('zemauth.can_view_account_agency_information'):
            required_fields.insert(2, 'agency')

        if breakdown == 'ad_group':
            required_fields.extend(['ad_group'])
            dimensions.extend(['ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['ad_group', 'title', 'image_url', 'image_hash', 'label', 'url'])
            dimensions.extend(['ad_group', 'content_ad'])
        required_fields.extend(['status'])
        if include_model_ids:
            required_fields = _include_model_ids(required_fields)
        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)
        order = _adjust_ordering(order, dimensions)
        fieldnames = _get_fieldnames(required_fields, additional_fields)
        conversion_goals = _get_conversion_goals(user, campaign)

        fieldnames = _extend_fieldnames(fieldnames, conversion_goals, additional_fields)

        results = _generate_rows(
            dimensions,
            start_date,
            end_date,
            user,
            order,
            breakdown == 'content_ad',
            conversion_goals,
            include_settings=True,
            campaign=campaign,
            source=filtered_sources)

        return get_csv_content(fieldnames, results)


class AdGroupAdsExport(object):

    def get_data(self, user, ad_group_id, filtered_sources, start_date, end_date,
                 order, additional_fields, breakdown=None, by_source=False, by_day=False, include_model_ids=False):

        ad_group = helpers.get_ad_group(user, ad_group_id)

        required_fields = ['start_date', 'end_date', 'account', 'campaign', 'ad_group']
        if user.has_perm('zemauth.can_view_account_agency_information'):
            required_fields.insert(2, 'agency')
        dimensions = []

        if breakdown == 'ad_group':
            dimensions.extend(['ad_group'])
        elif breakdown == 'content_ad':
            required_fields.extend(['title', 'image_url', 'image_hash', 'label', 'url'])
            dimensions.extend(['content_ad'])
        required_fields.extend(['status'])
        if include_model_ids:
            required_fields = _include_model_ids(required_fields)
        required_fields, dimensions = _include_breakdowns(required_fields, dimensions, by_day, by_source)
        order = _adjust_ordering(order, dimensions)
        fieldnames = _get_fieldnames(required_fields, additional_fields)
        conversion_goals = _get_conversion_goals(user, ad_group.campaign)
        fieldnames = _extend_fieldnames(fieldnames, conversion_goals, additional_fields)

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
    can_view_platform_cost_breakdown = request.user.has_perm('zemauth.can_view_platform_cost_breakdown')
    can_view_actual_costs = request.user.has_perm('zemauth.can_view_actual_costs')
    can_view_flat_fees = request.user.has_perm('zemauth.can_view_flat_fees')
    can_see_projections = request.user.has_perm('zemauth.can_see_projections')
    can_see_managers_in_accounts_table = request.user.has_perm('zemauth.can_see_managers_in_accounts_table')
    can_see_managers_in_campaigns_table = request.user.has_perm('zemauth.can_see_managers_in_campaigns_table')
    can_see_account_type = request.user.has_perm('zemauth.can_see_account_type')
    can_view_agency_margin = request.user.has_perm('zemauth.can_view_agency_margin')

    for f in fields:
        if f in ('margin', 'agency_total') and not can_view_agency_margin:
            continue
        if f in ('e_data_cost', 'e_media_cost',
                 'license_fee') and not can_view_platform_cost_breakdown:
            continue
        if f in ('data_cost', 'media_cost',
                 'license_fee') and not can_view_actual_costs:
            continue
        if f in ('total_fee', 'flat_fee',
                 'total_fee_projection') and not (can_view_flat_fees and can_view_platform_cost_breakdown):
            continue
        if f in ('allocated_budget', 'spend_projection', 'pacing', 'license_fee_projection',
                 'total_fee_projection') and not can_see_projections:
            continue
        if f in ('default_account_manager', 'default_sales_representative') and not can_see_managers_in_accounts_table:
            continue
        if f in ('campaign_manager',) and not can_see_managers_in_campaigns_table:
            continue
        if f in ('account_type',) and not can_see_account_type:
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
        include_model_ids=export_report.include_model_ids,
        campaign=export_report.campaign,
        account=export_report.account
    )


def get_report_from_request(request, account=None, campaign=None, ad_group=None, by_source=False):
    additional_fields = filter_allowed_fields(
        request,
        helpers.get_additional_columns(request.GET.get('additional_fields'))
    )

    granularity = get_granularity_from_type(request.GET.get('type'))
    view_filter = helpers.ViewFilter(request=request)

    return _get_report(
        request.user,
        helpers.get_stats_start_date(request.GET.get('start_date')),
        helpers.get_stats_end_date(request.GET.get('end_date')),
        filtered_sources=helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources')),
        view_filter=view_filter,
        order=request.GET.get('order') or 'name',
        additional_fields=additional_fields,
        granularity=granularity,
        breakdown=get_breakdown_from_granularity(granularity),
        by_source=by_source,
        by_day=request.GET.get('by_day') == 'true',
        include_model_ids=request.GET.get('include_model_ids') == 'true',
        ad_group=ad_group,
        campaign=campaign,
        account=account
    )


def _get_report(
        user,
        start_date,
        end_date,
        filtered_sources=None,
        view_filter=None,
        order=None,
        additional_fields=None,
        granularity=None,
        breakdown=None,
        by_day=False,
        by_source=False,
        include_model_ids=False,
        ad_group=None,
        campaign=None,
        account=None):

    if not user.has_perm('zemauth.can_include_model_ids_in_reports'):
        include_model_ids = False

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
        view_filter=view_filter,
        start_date=start_date,
        end_date=end_date,
        order=order,
        additional_fields=additional_fields,
        breakdown=breakdown,
        by_source=by_source,
        by_day=by_day,
        include_model_ids=include_model_ids,
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


def _get_report_contents(user, filtered_sources, view_filter, start_date, end_date, order, additional_fields,
                         breakdown, by_source, by_day, include_model_ids=False,
                         account_id=None, campaign_id=None, ad_group_id=None):
    arguments = {
        'user': user,
        'filtered_sources': filtered_sources,
        'start_date': start_date,
        'end_date': end_date,
        'order': order,
        'additional_fields': additional_fields,
        'breakdown': breakdown,
        'by_source': by_source,
        'by_day': by_day,
        'include_model_ids': include_model_ids
    }

    if account_id:
        arguments['account_id'] = account_id
        return AccountExport().get_data(**arguments)
    elif campaign_id:
        arguments['campaign_id'] = campaign_id
        return CampaignExport().get_data(**arguments)
    elif ad_group_id:
        arguments['ad_group_id'] = ad_group_id
        return AdGroupAdsExport().get_data(**arguments)

    arguments['view_filter'] = view_filter
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


def _should_show_all_fields_on_date(stat_date, first_stat_date):
    return first_stat_date is not None and stat_date == first_stat_date or stat_date.day == 1
