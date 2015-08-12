import datetime
import json
import logging

from utils import api_common
from utils import exc
from utils import statsd_helper

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

        bulk_objects = []
        try:
            data_blob = json.loads(request.body)
        except:
            logger.exception("Failed parsing request body")
            raise

        for entry in data_blob:
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
                bulk_objects.append(stats)
            except:
                logging.exception("Failed parsing content ad {blob}".format(blob=json.dumps(entry)))
                pass

        # TODO: setup transaction
        reports.models.ContentAdPostclickStats.objects.bulk_create(bulk_objects)

        return self.create_api_response({})


def _parse_duration(self, durstr):
    hours_str, minutes_str, seconds_str = durstr.replace('<', '').split(':')
    return int(seconds_str) + 60 * int(minutes_str) + 60 * 60 * int(hours_str)

