from dateutil import rrule

import dash.models
import reports.api
import reports.update
import reports.models

from reports.models import TRAFFIC_METRICS, POSTCLICK_METRICS, CONVERSION_METRICS


def refresh_demo_data(start_date, end_date):

    _refresh_stats_data(start_date, end_date)
    _refresh_conversion_data(start_date, end_date)


def _refresh_stats_data(start_date, end_date):
    daterange = rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date)

    for dt in daterange:
        for demo_ad_group in dash.models.AdGroup.demo_objects.all():
            demo2real = dash.models.DemoAdGroupRealAdGroup.objects.get(
                demo_ad_group=demo_ad_group
            )

            real_ad_group = demo2real.real_ad_group
            multiplication_factor = demo2real.multiplication_factor

            qs = reports.models.ArticleStats.objects.filter(
                datetime=dt,
                ad_group=real_ad_group
            )

            demo_rows = []
            for row in qs:
                d_row = {
                    'article': row.article,
                    'source': row.source
                }
                for metric in list(TRAFFIC_METRICS) + list(POSTCLICK_METRICS):
                    val = getattr(row, metric)
                    if val is not None:
                        val *= multiplication_factor  # all business growth occurs here
                    d_row[metric] = val
                demo_rows.append(d_row)

            reports.update.stats_update_adgroup_all(dt, demo_ad_group, demo_rows)


def _refresh_conversion_data(start_date, end_date):
    daterange = rrule.rrule(rrule.DAILY, dtstart=start_date, until=end_date)

    for dt in daterange:
        for demo_ad_group in dash.models.AdGroup.demo_objects.all():
            demo2real = dash.models.DemoAdGroupRealAdGroup.objects.get(
                demo_ad_group=demo_ad_group
            )

            real_ad_group = demo2real.real_ad_group
            multiplication_factor = demo2real.multiplication_factor

            qs = reports.models.GoalConversionStats.objects.filter(
                datetime=dt,
                ad_group=real_ad_group
            )

            demo_rows = []
            for row in qs:
                d_row = {
                    'article': row.article,
                    'source': row.source,
                    'goal_name': row.goal_name,
                }
                for metric in CONVERSION_METRICS:
                    val = getattr(row, metric)
                    if val is not None:
                        val *= multiplication_factor
                    d_row[metric] = val
                demo_rows.append(d_row)

            reports.update.goals_update_adgroup(dt, demo_ad_group, demo_rows)
