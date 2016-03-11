import dash.constants
import models
from reports import redshift

REPORT_GOAL_TYPES = [dash.constants.ConversionGoalType.GA, dash.constants.ConversionGoalType.OMNITURE]
PIXEL_GOAL_TYPE = dash.constants.ConversionGoalType.PIXEL


def transform_conversions(rows):
    results = []
    for row in rows:
        new_row = {}
        for key, val in row.iteritems():
            if key.startswith('conversions'):
                _, json_key = redshift.extract_json_key_parts(key)
                new_row.setdefault('conversions', {})
                new_row['conversions'][json_key] = val
                continue
            new_row[key] = val
        results.append(new_row)
    return results


def transform_conversion_goals(rows, conversion_goals):
    report_conversion_goals = [cg for cg in conversion_goals if cg.type in REPORT_GOAL_TYPES]
    touchpoint_conversion_goals = [cg for cg in conversion_goals if cg.type == PIXEL_GOAL_TYPE]

    for row in rows:
        for conversion_goal in report_conversion_goals:
            key = conversion_goal.get_stats_key()
            row[conversion_goal.get_view_key(conversion_goals)] = row.get('conversions', {}).get(key)

        for tp_conversion_goal in touchpoint_conversion_goals:
            goal_value = row.get('conversions', {}).get(tp_conversion_goal.name, None)
            if goal_value is None:
                # set the default - if tp_conv_stats result won't contain value, assume it's 0
                row[tp_conversion_goal.get_view_key(conversion_goals)] = 0
            else:
                row[tp_conversion_goal.get_view_key(conversion_goals)] = goal_value
        if 'conversions' in row:
            # mapping done, this is not needed anymore
            del row['conversions']


def merge_touchpoint_conversions_to_publishers_data(publishers_data, touchpoint_conversions):
    touchpoint_sources = [tp['source'] for tp in touchpoint_conversions]
    sources = models.Source.objects.filter(pk__in=touchpoint_sources)
    sources_by_id = {source.id: source for source in sources}

    publishers_data_by_key = {(p['exchange'], p['domain']): p for p in publishers_data}
    for tp in touchpoint_conversions:
        key = (sources_by_id[tp['source']].name.lower(), tp['publisher'])

        publisher = publishers_data_by_key[key]
        publisher['conversions'][tp['slug']] = tp['conversion_count']


def merge_touchpoint_conversion_to_publishers_for_total(total_data, touchpoint_conversions):
    for tp in touchpoint_conversions:
        total_data['conversions'][tp['slug']] = tp['conversion_count']
