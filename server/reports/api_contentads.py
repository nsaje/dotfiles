import collections
import dash
import datetime
import logging

from utils import exc

import dash.models
import reports.models

from django.db import transaction
from reports import models
from reports import aggregate_fields
from reports import api_helpers


logger = logging.getLogger(__name__)


def query(start_date, end_date, breakdown=None, **constraints):
    constraints = _preprocess_constraints(constraints)

    stats = models.ContentAdStats.objects.filter(
        date__gte=start_date, date__lte=end_date, **constraints)

    if breakdown:
        breakdown = _preprocess_breakdown(breakdown)
        stats = stats.values(*breakdown).annotate(**aggregate_fields.AGGREGATE_FIELDS)
        return [_transform_row(s) for s in stats]

    stats = stats.aggregate(**aggregate_fields.AGGREGATE_FIELDS)

    return _transform_row(stats)


def _preprocess_breakdown(breakdown):
    if not breakdown or len(set(breakdown) - api_helpers.DIMENSIONS) != 0:
        raise exc.ReportsQueryError('Invalid breakdown')

    breakdown_field_translate = {
        'ad_group': 'content_ad__ad_group'
    }

    breakdown = [] if breakdown is None else breakdown[:]

    fields = [breakdown_field_translate.get(field, field) for field in breakdown]

    return fields


def _preprocess_constraints(constraints):
    constraint_field_translate = {
        'ad_group': 'content_ad__ad_group',
        'campaign': 'content_ad__ad_group__campaign'
    }

    result = {}
    for k, v in constraints.iteritems():
        k = constraint_field_translate.get(k, k)

        if isinstance(v, collections.Sequence):
            result['{0}__in'.format(k)] = v
        else:
            result[k] = v

    return result


def _transform_row(row):
    result = {}
    for name, val in row.items():
        if name == 'content_ad__ad_group':
            name = 'ad_group'
        else:
            val = aggregate_fields.transform_val(name, val)
            name = aggregate_fields.transform_name(name)

        result[name] = val

    return result


def process_report(parsed_report_rows, report_type):
    # get all sources and their corresponding slugs
    # construct a dict from source tracking param to it's id
    sources = dash.models.Source.objects.all()
    track_source_map = {}
    for source in sources:
        track_source_map[source.tracking_slug] = source.id

    bulk_contentad_stats = []
    bulk_goal_conversion_stats = []
    for entry in parsed_report_rows:
        stats = _create_contentad_postclick_stats(entry, track_source_map)
        if stats is None:
            continue
        bulk_contentad_stats.append(stats)

        goal_conversion_stats = _create_contentad_goal_conversion_stats(entry, report_type, track_source_map)
        bulk_goal_conversion_stats.extend(goal_conversion_stats)

    with transaction.atomic():
        for obj in bulk_contentad_stats:
            reports.models.ContentAdPostclickStats.objects.filter(
                date=obj.date,
                content_ad__id=obj.content_ad_id,
                source__id=obj.source_id
            ).delete()

        for obj in bulk_goal_conversion_stats:
            reports.models.ContentAdGoalConversionStats.objects.filter(
                date=obj.date,
                content_ad__id=obj.content_ad_id,
                source__id=obj.source_id,
                goal_type=report_type,
            ).delete()

        for obj in bulk_contentad_stats:
            obj.save()

        for obj in bulk_goal_conversion_stats:
            obj.save()

        #print reports.models.ContentAdPostclickStats.objects.bulk_create(bulk_contentad_stats)
        #print reports.models.ContentAdGoalConversionStats.objects.bulk_create(bulk_goal_conversion_stats)


def _create_contentad_postclick_stats(entry, track_source_map):
    created_dt = datetime.datetime.utcnow()

    ga_report = entry.ga_row_dict
    try:
        report_date = entry.report_date
        visits = int(ga_report['Sessions'])
        bounce_rate = float(ga_report['Bounce Rate'].replace('%', '').replace(',', '')) / 100

        stats = reports.models.ContentAdPostclickStats(
            date=report_date,
            created_dt=created_dt,
            visits=visits,
            new_visits=int(ga_report['New Users']),
            bounced_visits=int(bounce_rate * visits),
            pageviews=int(round(float(ga_report['Pages / Session']) * visits)),
            total_time_on_site=visits * _parse_duration(ga_report['Avg. Session Duration']),
        )
        stats.source_id = track_source_map[entry.source_param]
        stats.content_ad_id = int(entry.content_ad_id)
        return stats
    except:
        logger.exception("Failed parsing content ad {blob}".format(
            blob=entry
        ))
        raise
    return None


def _create_contentad_goal_conversion_stats(entry, goal_type, track_source_map):
    created_dt = datetime.datetime.utcnow()
    try:
        report_date = entry.report_date
        stats = []
        for goal, values in entry.goals.iteritems():
            stat = reports.models.ContentAdGoalConversionStats(
                date=report_date,
                created_dt=created_dt,
                goal_type=goal_type,
                goal_name=goal,
                conversions=values['conversions'],
            )
            stat.source_id = track_source_map[entry.source_param]
            stat.content_ad_id = int(entry.content_ad_id)
            stats.append(stat)
        return stats
    except:
        logger.exception("Failed parsing content ad {blob}".format(
            blob=entry
        ))
        raise
    return []


def _parse_duration(durstr):
    hours_str, minutes_str, seconds_str = durstr.replace('<', '').split(':')
    return int(seconds_str) + 60 * int(minutes_str) + 60 * 60 * int(hours_str)
