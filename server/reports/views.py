import datetime
import json
import logging

from utils import api_common
from utils import exc
from utils import statsd_helper

from reports import constants

import dash.models
import reports.models

logger = logging.getLogger(__name__)

class GaContentAdReport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('reports.api', 'gacontentadreport_post')
    def post(self, request):
        if not request.user.has_perm('zemauth.contentadstats'):
            raise exc.AuthorizationError()

        # assuming objects are well formed here

        # get all sources and their corresponding slugs
        # construct a dict from source tracking param to it's id
        sources = dash.models.Source.objects.all()
        track_source_map = {}
        for source in sources:
            track_source_map[source.tracking_slug] = source.id

        created_dt = datetime.datetime.utcnow()

        try:
            data_blob = json.loads(request.body)
        except:
            logger.exception("Failed parsing request body")
            raise

        bulk_contentad_stats = []
        bulk_goal_conversion_stats = []
        for entry in data_blob:
            stats = _create_contentad_postclick_stats(entry)
            if stats is None:
                continue
            bulk_contentad_stats.append(stats)

            goal_conversion_stats = _create_contentad_goal_conversion_stats(entry, constants.GOOGLE_ANALYTICS)
            bulk_goal_conversion_stats.extend(goal_conversion_stats)

        reports.models.ContentAdPostclickStats.objects.bulk_create(bulk_contentad_stats)
        reports.models.ContentAdGoalConversionStats.objects.bulk_create(bulk_goal_conversion_stats)

        return self.create_api_response({})


def _create_contentad_postclick_stats(entry):
    ga_entry = entry['ga_report']
    try:
        report_date = datetime.datetime.strptime(entry['report_date'], "%Y-%m-%dT%H:%M:%S")

        visits = int(ga_report['Sessions'])
        bounce_rate = float(entry['Bounce Rate'].replace('%', '').replace(',', '')) / 100

        stats = reports.models.ContentAdPostclickStats(
            date=report_date,
            created_dt=created_dt,
            visits=visits,
            new_visits=int(entry['New Users']),
            bounced_visits=int(bounce_rate * visits),
            pageviews=int(round(float(ga_entry['Pages / Session']) * visits)),
            total_time_on_site=visits * _parse_duration(ga_entry['Avg. Session Duration']),
        )
        stats.source_id = track_source_map[entry['source_param']]
        stats.content_ad_id = int(entry['content_ad_id'])
        return stats
    except:
        logging.exception("Failed parsing content ad {blob}".format(blob=json.dumps(entry)))
    return None

def _create_contentad_goal_conversion_stats(entry, goal_type):
    ga_entry = entry['ga_report']
    try:
        report_date = datetime.datetime.strptime(entry['report_date'], "%Y-%m-%dT%H:%M:%S")

        visits = int(ga_report['Sessions'])
        bounce_rate = float(entry['Bounce Rate'].replace('%', '').replace(',', '')) / 100

        stats = []
        for goal in entry['goals']:
            stat = reports.models.ContentAdGoalConversionStats(
                date=report_date,
                created_dt=created_dt,
                goal_type=goal_type,
                goal_name=goal,
                visits=visits,
                new_visits=int(entry['New Users']),
                bounced_visits=int(bounce_rate * visits),
                pageviews=int(round(float(ga_entry['Pages / Session']) * visits)),
                total_time_on_site=visits * _parse_duration(ga_entry['Avg. Session Duration']),
                goal_conversions=goal['conversions'],
                goal_value=goal['value'],
            )
            stat.source_id = track_source_map[entry['source_param']]
            stat.content_ad_id = int(entry['content_ad_id'])
            stats.append(stats)
        return stats
    except:
        logging.exception("Failed parsing content ad {blob}".format(blob=json.dumps(entry)))
    return []

def _parse_duration(self, durstr):
    hours_str, minutes_str, seconds_str = durstr.replace('<', '').split(':')
    return int(seconds_str) + 60 * int(minutes_str) + 60 * 60 * int(hours_str)
