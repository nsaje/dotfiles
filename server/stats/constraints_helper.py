import copy

from django.db.models import Q
from utils.queryset_helper import simplify_query

import newrelic.agent

from dash import models

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
                                     filtered_agencies=None, filtered_account_types=None, only_used_sources=True):

    allowed_accounts = models.Account.objects.all()\
                                             .filter_by_user(user)\
                                             .filter_by_sources(filtered_sources)\
                                             .filter_by_agencies(filtered_agencies)\
                                             .filter_by_account_types(filtered_account_types)
    allowed_accounts = simplify_query(allowed_accounts)

    allowed_campaigns = models.Campaign.objects.filter(account__in=allowed_accounts)\
                                               .filter_by_user(user)\
                                               .filter_by_sources(filtered_sources)
    allowed_campaigns = simplify_query(allowed_campaigns)

    # accounts tab
    if constants.get_base_dimension(breakdown) == 'account_id':
        # exclude archived accounts/campaigns only when on accounts tab
        allowed_accounts = simplify_query(allowed_accounts.exclude_archived(show_archived))
        allowed_campaigns = simplify_query(allowed_campaigns.exclude_archived(show_archived))

    constraints = {
        'allowed_accounts': allowed_accounts,
        'allowed_campaigns': allowed_campaigns,
    }

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group__campaign__account__in=allowed_accounts)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    constraints.update(_get_basic_constraints(start_date, end_date, show_archived, filtered_sources))

    return constraints


@newrelic.agent.function_trace()
def prepare_account_constraints(user, account, breakdown, start_date, end_date, filtered_sources,
                                show_archived=False, only_used_sources=True):
    allowed_campaigns = account.campaign_set.all()\
                                            .filter_by_user(user)\
                                            .filter_by_sources(filtered_sources)

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

    constraints.update(_get_basic_constraints(start_date, end_date, show_archived, filtered_sources))

    return constraints


@newrelic.agent.function_trace()
def prepare_campaign_constraints(user, campaign, breakdown, start_date, end_date, filtered_sources,
                                 show_archived=False, only_used_sources=True):
    allowed_ad_groups = campaign.adgroup_set.all().exclude_archived(show_archived)
    constraints = {
        'campaign': campaign,
        'account': campaign.account,
        'allowed_ad_groups': allowed_ad_groups,
        'allowed_content_ads': models.ContentAd.objects.filter(
            ad_group__in=allowed_ad_groups).exclude_archived(show_archived)
    }

    constraints.update(_get_basic_constraints(
        start_date, end_date, show_archived, filtered_sources))

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group__campaign_id=campaign.id)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    return constraints


@newrelic.agent.function_trace()
def prepare_ad_group_constraints(user, ad_group, breakdown, start_date, end_date, filtered_sources,
                                 show_archived=False, only_used_sources=True,
                                 show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ALL):
    constraints = {
        'ad_group': ad_group,
        'campaign': ad_group.campaign,
        'account': ad_group.campaign.account,
        'allowed_content_ads': models.ContentAd.objects.filter(
            ad_group=ad_group).exclude_archived(show_archived)
    }

    if only_used_sources:
        ad_group_sources = models.AdGroupSource.objects.filter(ad_group_id=ad_group.id)
        filtered_sources = narrow_filtered_sources(filtered_sources, ad_group_sources)

    blacklisted_publishers = models.PublisherBlacklist.objects.filter(
        Q(ad_group=ad_group) |
        Q(campaign=ad_group.campaign) |
        Q(account=ad_group.campaign.account) |
        Q(everywhere=True)
    ).filter_by_sources(filtered_sources)
    constraints['publisher_blacklist'] = blacklisted_publishers
    constraints['publisher_blacklist_filter'] = show_blacklisted_publishers

    constraints.update(_get_basic_constraints(
        start_date, end_date, show_archived, filtered_sources))

    return constraints


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
