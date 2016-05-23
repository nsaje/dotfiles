import collections

from dash import models

from stats import constants
from stats import helpers


UNKNOWN = 'Unknown'


def augment(breakdown, stats_rows, target_dimension):

    if target_dimension == constants.StructureDimension.ACCOUNT:
        augment_accounts(stats_rows)

    if target_dimension == constants.StructureDimension.CAMPAIGN:
        augment_campaigns(stats_rows)

    if target_dimension == constants.StructureDimension.AD_GROUP:
        augment_ad_groups(stats_rows)

    if target_dimension == constants.StructureDimension.CONTENT_AD:
        augment_content_ads(stats_rows)

    if target_dimension == constants.StructureDimension.SOURCE:
        augment_source(stats_rows)

    for row in stats_rows:
        row['breakdown_id'] = helpers.create_breakdown_id(breakdown, row)
        row['parent_breakdown_id'] = helpers.create_breakdown_id(breakdown[:-1], row) if breakdown else None


def augment_accounts(stats_rows):
    rows_by_id = collections.defaultdict(list)
    for row in stats_rows:
        rows_by_id[row['account_id']].append(row)

    accounts = models.Account.objects.filter(pk__in=rows_by_id.keys())
    account_by_id = {x.pk: x for x in accounts}

    for account_id, rows in rows_by_id.items():
        account = account_by_id.get(account_id)
        for row in rows:
            row['account_name'] = account.name if account else UNKNOWN


def augment_campaigns(stats_rows):
    rows_by_id = collections.defaultdict(list)
    for row in stats_rows:
        rows_by_id[row['campaign_id']].append(row)

    campaigns = models.Campaign.objects.filter(pk__in=rows_by_id.keys())
    campaign_by_id = {x.pk: x for x in campaigns}

    for campaign_id, rows in rows_by_id.items():
        campaign = campaign_by_id.get(campaign_id)
        for row in rows:
            row['campaign_name'] = campaign.name if campaign else UNKNOWN


def augment_ad_groups(stats_rows):
    rows_by_id = collections.defaultdict(list)
    for row in stats_rows:
        rows_by_id[row['ad_group_id']].append(row)

    ad_groups = models.AdGroup.objects.filter(pk__in=rows_by_id.keys())
    ad_group_by_id = {x.pk: x for x in ad_groups}

    for ad_group_id, rows in rows_by_id.items():
        ad_group = ad_group_by_id.get(ad_group_id)
        for row in rows:
            row['ad_group_name'] = ad_group.name if ad_group else UNKNOWN


def augment_content_ads(stats_rows):
    rows_by_id = collections.defaultdict(list)
    for row in stats_rows:
        rows_by_id[row['content_ad_id']].append(row)

    content_ads = models.ContentAd.objects.filter(pk__in=rows_by_id.keys())
    content_ad_by_id = {x.pk: x for x in content_ad_by_id}

    for content_ad_id, rows in rows_by_id.items():
        content_ad = content_ad_by_id.get(content_ad_id)
        for row in rows:
            row['content_ad_title'] = content_ad.title if content_ad else UNKNOWN


def augment_source(stats_rows):
    rows_by_id = collections.defaultdict(list)
    for row in stats_rows:
        rows_by_id[row['source_id']].append(row)

    sources = models.Source.objects.filter(pk__in=rows_by_id.keys())
    source_by_id = {x.pk: x for x in sources}

    for source_id, rows in rows_by_id.items():
        source = source_by_id.get(source_id)
        for row in rows:
            row['source_name'] = source.name if source else UNKNOWN
