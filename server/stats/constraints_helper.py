import copy

import newrelic.agent

from utils.queryset_helper import simplify_query
from dash import models
from core.publisher_groups import publisher_group_helpers
from stats import constants
import dash.constants


def narrow_filtered_sources(sources, ad_group_sources):
    sources = sources.filter(
        pk__in=list(ad_group_sources.distinct('source_id').values_list('source_id', flat=True)))
    return simplify_query(sources)


def _get_basic_constraints(start_date, end_date, show_archived, filtered_sources):
    return {
        'date__gte': start_date,
        'date__lte': end_date,
        'show_archived': show_archived,
        'filtered_sources': filtered_sources,
    }


@newrelic.agent.function_trace()
def prepare_all_accounts_constraints(user, breakdown, start_date, end_date, filtered_sources, show_archived=False,
                                     filtered_agencies=None, filtered_account_types=None, filtered_accounts=None,
                                     only_used_sources=True,
                                     show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL):

    allowed_accounts = models.Account.objects.all()\
                                             .filter_by_user(user)\
                                             .filter_by_sources(filtered_sources)\
                                             .filter_by_agencies(filtered_agencies)\
                                             .filter_by_account_types(filtered_account_types)

    if filtered_accounts:
        allowed_accounts = allowed_accounts.filter(id__in=filtered_accounts.values_list('id', flat=True))

    allowed_campaigns = models.Campaign.objects.filter(account__in=allowed_accounts)\
                                               .filter_by_sources(filtered_sources)

    # accounts tab
    if constants.get_base_dimension(breakdown) == 'account_id':
        # exclude archived accounts/campaigns only when on accounts tab
        allowed_accounts = allowed_accounts.exclude_archived(show_archived)
        allowed_campaigns = allowed_campaigns.exclude_archived(show_archived)

    constraints = {
        'allowed_accounts': allowed_accounts,
        'allowed_campaigns': allowed_campaigns,
    }

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group__campaign__account__in=allowed_accounts)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    add_publisher_constraints(
        constraints, filtered_sources, show_blacklisted_publishers,
        None, None,
        None, None,
        None, None,
    )

    constraints.update(_get_basic_constraints(start_date, end_date, show_archived, filtered_sources))

    return constraints


@newrelic.agent.function_trace()
def prepare_account_constraints(user, account, breakdown, start_date, end_date, filtered_sources,
                                filtered_campaigns=None, show_archived=False, only_used_sources=True,
                                show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL):
    allowed_campaigns = account.campaign_set.all()\
                                            .filter_by_user(user)\
                                            .filter_by_sources(filtered_sources)

    if filtered_campaigns:
        allowed_campaigns = allowed_campaigns.filter(id__in=filtered_campaigns.values_list('id', flat=True))

    allowed_ad_groups = models.AdGroup.objects.filter(campaign__in=allowed_campaigns)

    # campaigns tab
    if constants.get_base_dimension(breakdown) == 'campaign_id':
        allowed_campaigns = allowed_campaigns.exclude_archived(show_archived)
        allowed_ad_groups = allowed_ad_groups.exclude_archived(show_archived)

    constraints = {
        'account': account,
        'allowed_campaigns': simplify_query(allowed_campaigns),
        'allowed_ad_groups': simplify_query(allowed_ad_groups),
    }

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group__campaign__account_id=account.id)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    account_settings = account.get_current_settings()

    add_publisher_constraints(
        constraints, filtered_sources, show_blacklisted_publishers,
        None, None,
        None, None,
        account, account_settings,
    )

    constraints.update(_get_basic_constraints(start_date, end_date, show_archived, filtered_sources))

    return constraints


@newrelic.agent.function_trace()
def prepare_campaign_constraints(user, campaign, breakdown, start_date, end_date, filtered_sources,
                                 filtered_ad_groups=None, show_archived=False, only_used_sources=True,
                                 show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL):
    allowed_ad_groups = campaign.adgroup_set.all().exclude_archived(show_archived)
    if filtered_ad_groups:
        allowed_ad_groups = allowed_ad_groups.filter(id__in=filtered_ad_groups.values_list('id', flat=True))

    constraints = {
        'campaign': campaign,
        'account': campaign.account,
        'allowed_ad_groups': allowed_ad_groups,
        'allowed_content_ads': models.ContentAd.objects.filter(
            ad_group__in=allowed_ad_groups).exclude_archived(show_archived)
    }

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group__campaign_id=campaign.id)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    campaign_settings = campaign.get_current_settings()
    account_settings = campaign.account.get_current_settings()

    add_publisher_constraints(
        constraints, filtered_sources, show_blacklisted_publishers,
        None, None,
        campaign, campaign_settings,
        campaign.account, account_settings,
    )

    constraints.update(_get_basic_constraints(
        start_date, end_date, show_archived, filtered_sources))

    return constraints


@newrelic.agent.function_trace()
def prepare_ad_group_constraints(user, ad_group, breakdown, start_date, end_date, filtered_sources,
                                 filtered_content_ads=None, show_archived=False, only_used_sources=True,
                                 show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL):
    allowed_content_ads = models.ContentAd.objects.filter(ad_group=ad_group).exclude_archived(show_archived)
    if filtered_content_ads:
        allowed_content_ads = allowed_content_ads.filter(id__in=filtered_content_ads.values_list('id', flat=True))

    constraints = {
        'ad_group': ad_group,
        'campaign': ad_group.campaign,
        'account': ad_group.campaign.account,
        'allowed_content_ads': allowed_content_ads,
    }

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group_id=ad_group.id)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    ad_group_settings = ad_group.get_current_settings()
    campaign_settings = ad_group.campaign.get_current_settings()
    account_settings = ad_group.campaign.account.get_current_settings()

    add_publisher_constraints(
        constraints, filtered_sources, show_blacklisted_publishers,
        ad_group, ad_group_settings,
        ad_group.campaign, campaign_settings,
        ad_group.campaign.account, account_settings,
    )

    constraints.update(_get_basic_constraints(
        start_date, end_date, show_archived, filtered_sources))

    return constraints


def add_publisher_constraints(constraints, filtered_sources, show_blacklisted_publishers,
                              ad_group, ad_group_settings,
                              campaign, campaign_settings,
                              account, account_settings):
    blacklists, whitelists = publisher_group_helpers.concat_publisher_group_targeting(
        ad_group, ad_group_settings,
        campaign, campaign_settings,
        account, account_settings
    )

    publisher_group_targeting = publisher_group_helpers.get_publisher_group_targeting_dict(
        ad_group, ad_group_settings,
        campaign, campaign_settings,
        account, account_settings
    )

    blacklisted_entries = models.PublisherGroupEntry.objects.filter(publisher_group_id__in=blacklists)\
                                                            .filter_by_sources(filtered_sources, include_wo_source=True)
    whitelisted_entries = models.PublisherGroupEntry.objects.filter(publisher_group_id__in=whitelists)\
                                                            .filter_by_sources(filtered_sources, include_wo_source=True)

    constraints['publisher_blacklist'] = blacklisted_entries
    constraints['publisher_whitelist'] = whitelisted_entries
    constraints['publisher_group_targeting'] = publisher_group_targeting
    constraints['publisher_blacklist_filter'] = show_blacklisted_publishers


def get_allowed_constraints_field(target_dimension):
    if target_dimension == 'account_id':
        return 'allowed_accounts'
    elif target_dimension == 'campaign_id':
        return 'allowed_campaigns'
    elif target_dimension == 'ad_group_id':
        return 'allowed_ad_groups'
    elif target_dimension == 'content_ad_id':
        return 'allowed_content_ads'
    elif target_dimension == 'source_id':
        return 'filtered_sources'


def narrow_allowed_target_field(constraints, breakdown):
    parent_dimension = constants.get_base_dimension(breakdown)
    ad_group_sources = None

    if parent_dimension == 'account_id':
        constraints['allowed_campaigns'] = constraints['allowed_campaigns'].filter(
            account__in=constraints['allowed_accounts'])
        ad_group_sources = models.AdGroupSource.objects.filter(
            ad_group__campaign__account__in=constraints['allowed_accounts'])
    elif parent_dimension == 'campaign_id':
        constraints['allowed_ad_groups'] = constraints['allowed_ad_groups'].filter(
            campaign__in=constraints['allowed_campaigns'])
        ad_group_sources = models.AdGroupSource.objects.filter(
            ad_group__campaign__in=constraints['allowed_campaigns'])
    elif parent_dimension == 'ad_group_id':
        constraints['allowed_content_ads'] = constraints['allowed_content_ads'].filter(
            ad_group__in=constraints['allowed_ad_groups'])
        ad_group_sources = models.AdGroupSource.objects.filter(
            ad_group__in=constraints['allowed_ad_groups'])
    elif parent_dimension == 'source_id':
        for allowed_field in ('allowed_accounts', 'allowed_campaigns', 'allowed_ad_groups', 'publisher_blacklist'):
            if allowed_field in constraints:
                constraints[allowed_field] = constraints[allowed_field].filter_by_sources(
                    constraints['filtered_sources'])

    if constants.get_target_dimension(breakdown) == 'source_id' and ad_group_sources is not None:
        constraints['filtered_sources'] = narrow_filtered_sources(constraints['filtered_sources'], ad_group_sources)


def reduce_to_parent(breakdown, constraints, parent=None):
    constraints = copy.copy(constraints)

    # reduce parents
    for dimension in breakdown[:-1]:
        qs_field = get_allowed_constraints_field(dimension)
        constraints[qs_field] = constraints[qs_field].filter(pk=parent[dimension])

    if len(breakdown) > 1:
        narrow_allowed_target_field(constraints, breakdown)

    return constraints


def get_uses_bcm_v2(user, constraints):
    if constraints.get('account'):
        return constraints['account'].uses_bcm_v2
    elif 'allowed_accounts' in constraints:
        # all accounts - in case user is querying all accounts but she can also view other accounts then
        # behave as non-bcmv2
        accessible_non_bcm_accounts = models.Account.objects.filter_by_user(user)\
                                                            .exclude_archived()\
                                                            .filter(uses_bcm_v2=False)\
                                                            .exists()
        if accessible_non_bcm_accounts:
            return False

        return all(constraints['allowed_accounts'].values_list('uses_bcm_v2', flat=True))
    return False
