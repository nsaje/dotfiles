import collections
import datetime

from dash import models
from dash import constants as dash_constants
from dash import campaign_goals as dash_campaign_goals
from reports.api import row_has_conversion_goal_data, row_has_postclick_data, row_has_traffic_data

from stats import constants
from stats import helpers


UNKNOWN = 'Unknown'


def augment(breakdown, rows):
    target_dimension = constants.get_target_dimension(breakdown)

    # TODO not fully supported, value is wrong
    remove_status = breakdown == ['content_ad_id', 'source_id'] or breakdown == ['source_id', 'content_ad_id']

    for row in rows:
        row['breakdown_id'] = helpers.encode_breakdown_id(breakdown, row)
        row['parent_breakdown_id'] = helpers.encode_breakdown_id(
            constants.get_parent_breakdown(breakdown), row) if breakdown else None

        if target_dimension in constants.DeliveryDimension._ALL:
            augment_row_delivery(row, target_dimension)

        if target_dimension in constants.TimeDimension._ALL:
            augment_row_time(row, target_dimension)

        row['breakdown_name'] = row['name']

        if remove_status:
            row.pop('status', None)
            row.pop('state', None)


def cleanup(rows, target_dimension, constraints):
    to_remove = []

    # remove rows of deprecated sources without stats
    if target_dimension == 'source_id':
        deprecated_source_ids = list(
            constraints['filtered_sources'].filter(deprecated=True).values_list('pk', flat=True))
        if deprecated_source_ids:
            for row in rows:
                if row['source_id'] in deprecated_source_ids and\
                   not row_has_traffic_data(row) and\
                   not row_has_postclick_data(row) and\
                   not row_has_conversion_goal_data(row):
                    to_remove.append(row)

    for row in to_remove:
        rows.remove(row)


def augment_row_delivery(row, target_dimension):

    mapping = {
        constants.DeliveryDimension.DEVICE: dash_constants.DeviceType,
        constants.DeliveryDimension.AGE: dash_constants.AgeGroup,
        constants.DeliveryDimension.GENDER: dash_constants.Gender,
        constants.DeliveryDimension.AGE_GENDER: dash_constants.AgeGenderGroup,
        constants.DeliveryDimension.DMA: dash_constants.DMA,
    }

    if target_dimension in mapping and row[target_dimension]:
        row['name'] = mapping[target_dimension].get_text(row[target_dimension])
    else:
        row['name'] = row[target_dimension] or UNKNOWN


def augment_row_time(row, target_dimension):
    if target_dimension == constants.TimeDimension.DAY:
        date = row[constants.TimeDimension.DAY]
        row['name'] = date.isoformat()

    if target_dimension == constants.TimeDimension.WEEK:
        date = row[constants.TimeDimension.WEEK]
        row['name'] = "Week {} - {}".format(
            date.isoformat(), (date + datetime.timedelta(days=6)).isoformat())

    if target_dimension == constants.TimeDimension.MONTH:
        date = row[constants.TimeDimension.MONTH]
        row['name'] = "Month {}/{}".format(date.month, date.year)
