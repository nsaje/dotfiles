import collections

from dash import models

from stats import constants
from stats import helpers


def augment(breakdown, stats_rows, target_dimension):
    rows_by_obj_ids = _get_rows_by_obj_ids(stats_rows, target_dimension)
    objs_by_id = _get_needed_objs(rows_by_obj_ids)

    def rows(dimension):
        # helper for iterating through rows of the selected dimension
        for obj_id, rows in rows_by_obj_ids[dimension].iteritems():
            for row in rows:
                yield row, objs_by_id[dimension][obj_id], obj_id

    # only the targeted dimension will be selected here
    if 'account_id' in rows_by_obj_ids:
        for row, account, _ in rows('account_id'):
            row['account_name'] = account.name if account else 'Unknown'

    if 'campaign_id' in rows_by_obj_ids:
        for row, campaign, _ in rows('campaign_id'):
            row['campaign_name'] = campaign.name if campaign else 'Unknown'

    if 'ad_group_id' in rows_by_obj_ids:
        for row, ad_group, _ in rows('ad_group_id'):
            row['ad_group_name'] = ad_group.name if ad_group else 'Unknown'

    if 'content_ad_id' in rows_by_obj_ids:
        for row, content_ad, _ in rows('content_ad_id'):
            row['content_ad_title'] = content_ad.title if content_ad else 'Unknown'

    if 'source_id' in rows_by_obj_ids:
        for row, source, _ in rows('source_id'):
            row['source_name'] = source.name if source else 'Unknown'

    for row in stats_rows:
        row['breakdown_id'] = helpers.create_breakdown_id(breakdown, row)

def _get_rows_by_obj_ids(stats_rows, target_dimension):
    """
    Collect rows by targeted dimension id.
    """

    rows_by_obj_ids = collections.defaultdict(lambda: collections.defaultdict(list))

    for row in stats_rows:

        if target_dimension == constants.StructureDimension.ACCOUNT and 'account_id' in row:
            rows_by_obj_ids['account_id'][row['account_id']].append(row)

        if target_dimension == constants.StructureDimension.CAMPAIGN and 'campaign_id' in row:
            rows_by_obj_ids['campaign_id'][row['campaign_id']].append(row)

        if target_dimension == constants.StructureDimension.AD_GROUP and 'ad_group_id' in row:
            rows_by_obj_ids['ad_group_id'][row['ad_group_id']].append(row)

        if target_dimension == constants.StructureDimension.CONTENT_AD and 'content_ad_id' in row:
            rows_by_obj_ids['content_ad_id'][row['content_ad_id']].append(row)

        if target_dimension == constants.StructureDimension.SOURCE and 'source_id' in row:
            rows_by_obj_ids['source_id'][row['source_id']].append(row)

        if target_dimension == constants.StructureDimension.PUBLISHER and 'publisher' in row:
            rows_by_obj_ids['publisher'][row['publisher']].append(row)

    return rows_by_obj_ids


def _get_needed_objs(rows_by_obj_ids):
    """
    Load objects for rows by dimension ids.
    """

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

