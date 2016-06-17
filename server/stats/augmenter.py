import collections
import datetime

from dash import models
from dash import constants as dash_constants

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
        row['breakdown_name'] = row[constants.get_dimension_name_key(target_dimension)]
        row['parent_breakdown_id'] = helpers.create_breakdown_id(
            constants.get_parent_breakdown(breakdown), row) if breakdown else None

        augment_row_delivery(row)
        augment_row_time(row)


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
    content_ad_by_id = {x.pk: x for x in content_ads}

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


def augment_row_delivery(row):

    mapping = {
        constants.DeliveryDimension.DEVICE: dash_constants.DeviceType,
        constants.DeliveryDimension.AGE: dash_constants.AgeGroup,
        constants.DeliveryDimension.GENDER: dash_constants.Gender,
        constants.DeliveryDimension.AGE_GENDER: dash_constants.AgeGenderGroup,
    }

    for dimension, const_class in mapping.iteritems():
        if dimension in row:
            row[dimension] = const_class.get_text(row[dimension])

    for dimension in constants.DeliveryDimension._ALL:
        if dimension in row and not row[dimension]:
            row[dimension] = UNKNOWN


def augment_row_time(row):

    if constants.TimeDimension.DAY in row:
        date = row[constants.TimeDimension.DAY]
        row[constants.TimeDimension.DAY] = date.isoformat()

    if constants.TimeDimension.WEEK in row:
        date = row[constants.TimeDimension.WEEK]
        row[constants.TimeDimension.WEEK] = "Week {} - {}".format(date.isoformat(),
                                                                  (date + datetime.timedelta(days=6)).isoformat())

    if constants.TimeDimension.MONTH in row:
        date = row[constants.TimeDimension.MONTH]
        row[constants.TimeDimension.MONTH] = "Month {}/{}".format(date.month, date.year)


def filter_columns_by_permission(user, rows, breakdown, target_dimension):
    # TODO remove columns that user doesn't have a permission for
    # can use reports.api_helpers
    pass
