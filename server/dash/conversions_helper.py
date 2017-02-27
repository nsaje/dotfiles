import copy

import dash.constants
import models
from reports import redshift

REPORT_GOAL_TYPES = [dash.constants.ConversionGoalType.GA, dash.constants.ConversionGoalType.OMNITURE]
PIXEL_GOAL_TYPE = dash.constants.ConversionGoalType.PIXEL


def group_conversions(rows):
    results = []
    for row in rows:
        new_row = {}
        for key, val in row.iteritems():
            if key.startswith('conversions'):
                _, json_key = redshift.extract_json_key_parts(key)
                new_row.setdefault('conversions', {})
                new_row['conversions'][json_key] = val
            else:
                new_row[key] = val
        results.append(new_row)
    return results


def transform_to_conversion_goals(rows, conversion_goals, pixels):
    report_conversion_goals = [cg for cg in conversion_goals if cg.type in REPORT_GOAL_TYPES]

    for row in rows:
        for conversion_goal in report_conversion_goals:
            key = conversion_goal.get_stats_key()
            row[conversion_goal.get_view_key(conversion_goals)] = row.get('conversions', {}).get(key)

        if pixels:
            for pixel in pixels:
                for conversion_window in dash.constants.ConversionWindows.get_all():
                    key = (pixel.slug, pixel.account_id, conversion_window)
                    # set the default - if tp_conversion_goal result won't contain value, assume it's 0
                    goal_value = row.get('conversions', {}).get(key, 0)
                    view_key = pixel.get_view_key(conversion_window)
                    avg_cost_key = 'avg_cost_per_' + view_key
                    row[view_key] = goal_value
                    row[avg_cost_key] = None
                    e_media_cost = row.get('e_media_cost')
                    if e_media_cost is not None and goal_value:
                        row[avg_cost_key] = float(e_media_cost) / goal_value

        if 'conversions' in row:
            # mapping done, this is not needed anymore
            del row['conversions']


def convert_constraint_exchanges_to_source_ids(constraints):
    if 'exchange' not in constraints:
        return constraints

    constraints = copy.copy(constraints)

    exchanges = constraints['exchange']
    constraints['source'] = list(models.Source.objects.filter(bidder_slug__in=exchanges).values_list('id', flat=True))
    del(constraints['exchange'])

    return constraints
