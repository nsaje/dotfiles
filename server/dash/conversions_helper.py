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
                continue
            new_row[key] = val
        results.append(new_row)
    return results


def transform_to_conversion_goals(rows, conversion_goals):
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


def merge_touchpoint_conversions_to_publishers_data(publishers_data,
                                                    touchpoint_conversions,
                                                    publisher_breakdown_fields,
                                                    touchpoint_breakdown_fields):
    if touchpoint_conversions:
        def create_key(value, fields):
            return tuple(value[field] for field in fields)

        # if source in touchpoint field then do mapping from id to bidder_slug
        if 'source' in touchpoint_breakdown_fields:
            touchpoint_sources = [tp['source'] for tp in touchpoint_conversions]
            sources = models.Source.objects.filter(pk__in=touchpoint_sources).values('id', 'bidder_slug')
            sources_by_id = {source['id']: source['bidder_slug'] for source in sources}

            for tp in touchpoint_conversions:
                tp['source'] = sources_by_id[tp['source']]

        publishers_data_by_key = {create_key(p, publisher_breakdown_fields): p for p in publishers_data}
        touchpoint_data_by_key = {create_key(t, touchpoint_breakdown_fields): t for t in touchpoint_conversions}

        for key, val in touchpoint_data_by_key.iteritems():
            publisher = publishers_data_by_key.get(key, None)

            # TODO matijav 14.03.2016 fix this
            # if publisher doesn't exist create it from touchpoint data
            # if publisher is None:
            #     publisher = {}
            #     for i in range(len(publisher_breakdown_fields)):
            #         publisher[publisher_breakdown_fields[i]] = val[touchpoint_breakdown_fields[i]]
            #
            #     publishers_data_by_key[create_key(publisher, publisher_breakdown_fields)] = publisher
            #     publishers_data.append(publisher)

            if publisher:
                publisher.setdefault('conversions', {})
                publisher['conversions'][val['slug']] = val['conversion_count']
