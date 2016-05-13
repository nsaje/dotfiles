import copy
import collections

from dash import models


def extract_stats_constraints(constraints):
    """
    Remove any constraints that are not part of the stats query.
    """
    constraints = copy.copy(constraints)

    del constraints['show_archived']

    return constraints


def get_rows_by_obj_ids(stats_rows):

    rows_by_obj_ids = collections.defaultdict(lambda: collections.defaultdict(list))

    # collect objects that need to be augmented
    for row in stats_rows:

        # TODO could this sorting be a memory bottleneck?
        # should rows be indexed and only indices stored?
        # but if references are stored than it should be no problem

        if 'account_id' in row:
            rows_by_obj_ids['account_id'][row['account_id']].append(row)

        if 'campaign_id' in row:
            rows_by_obj_ids['campaign_id'][row['campaign_id']].append(row)

        if 'ad_group_id' in row:
            rows_by_obj_ids['ad_group_id'][row['ad_group_id']].append(row)

        if 'content_ad_id' in row:
            rows_by_obj_ids['content_ad_id'][row['content_ad_id']].append(row)

        if 'source_id' in row:
            rows_by_obj_ids['source_id'][row['source_id']].append(row)

        if 'publisher' in row:
            rows_by_obj_ids['publisher'][row['publisher']].append(row)

    return rows_by_obj_ids


def get_needed_objs(rows_by_obj_ids):

    objects_dict = collections.defaultdict(set)

    accounts = None
    campaigns = None
    ad_groups = None
    content_ads = None
    sources = None

    if 'account_id' in rows_by_obj_ids:
        ids = rows_by_obj_ids['account_id']
        accounts = models.Account.objects.filter(pk__in=ids)
        objects_dict['account_id'] = {x.id: x for x in accounts}

    if 'campaign_id' in rows_by_obj_ids:
        ids = rows_by_obj_ids['campaign_id']
        campaigns = models.Campaign.objects.filter(pk__in=ids)
        objects_dict['campaign_id'] = {x.id: x for x in campaigns}

    if 'ad_group_id' in rows_by_obj_ids:
        ids = rows_by_obj_ids['ad_group_id']
        ad_groups = models.AdGroup.objects.filter(pk__in=ids)
        objects_dict['ad_group_id'] = {x.id: x for x in ad_groups}

    if 'content_ad_id' in rows_by_obj_ids:
        ids = rows_by_obj_ids['content_ad_id']
        content_ads = models.ContentAd.objects.filter(pk__in=ids)
        objects_dict['content_ad_id'] = {x.id: x for x in content_ads}

    if 'source_id' in rows_by_obj_ids:
        ids = rows_by_obj_ids['source_id']
        sources = models.Source.objects.filter(pk__in=ids)
        objects_dict['source_id'] = {x.id: x for x in sources}

    # TODO data for status and running status

    return objects_dict


def augment(stats_rows):
    # TODO constants for other dimensions (age?), unknown
    # TODO can data between dimensions be shared? I think not - as
    # upper dimension needs a superset

    rows_by_obj_ids = get_rows_by_obj_ids(stats_rows)
    objs_by_id = get_needed_objs(rows_by_obj_ids)

    def rows(dimension):
        for obj_id, rows in rows_by_obj_ids[dimension].iteritems():
            for row in rows:
                yield row, objs_by_id[dimension][obj_id], obj_id

    if 'account_id' in rows_by_obj_ids:
        for row, account, _ in rows('account_id'):
            row['account_name'] = account.name

    if 'campaign_id' in rows_by_obj_ids:
        for row, campaign, _ in rows('campaign_id'):
            row['campaign_name'] = campaign.name

    if 'ad_group_id' in rows_by_obj_ids:
        for row, ad_group, _ in rows('ad_group_id'):
            row['ad_group_name'] = ad_group.name

    if 'content_ad_id' in rows_by_obj_ids:
        for row, content_ad, _ in rows('content_ad_id'):
            row['content_ad_title'] = content_ad.title

    if 'source_id' in rows_by_obj_ids:
        for row, source, _ in rows('source_id'):
            row['source_name'] = source.name
