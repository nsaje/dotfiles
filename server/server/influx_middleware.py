from django.db import connection
import influx
import logging

from utils import influx_helper

logger = logging.getLogger(__name__)


def queries_to_influx(get_response):

    def middleware(request):
        connection.force_debug_cursor = True

        response = get_response(request)

        try:
            if len(connection.queries) > 0:
                total_time = 0
                queries_per_verb = {
                    'SELECT': 0,
                    'INSERT': 0,
                    'UPDATE': 0,
                    'DELETE': 0,
                    'OTHER': 0,
                }

                for query in connection.queries:
                    query_time = query.get('time')
                    if query_time is None:
                        # django-debug-toolbar monkeypatches the connection
                        # cursor wrapper and adds extra information in each
                        # item in connection.queries. The query time is stored
                        # under the key "duration" rather than "time" and is
                        # in milliseconds, not seconds.
                        query_time = query.get('duration', 0) / 1000
                    total_time += float(query_time)
                    try:
                        queries_per_verb[query['sql'][:6]] += 1
                    except KeyError:
                        queries_per_verb['OTHER'] += 1

                path = influx_helper.clean_path(request.path)

                influx.timing(
                    'queries.timer',
                    total_time,
                    path=path,
                    method=request.method,
                    status=str(response.status_code),
                )
                influx.timing(
                    'queries.count',
                    len(connection.queries),
                    path=path,
                    method=request.method,
                    status=str(response.status_code),
                )
                for verb, count in queries_per_verb.items():
                    influx.timing(
                        'queries.count',
                        count,
                        verb=verb,
                        path=path,
                        method=request.method,
                        status=str(response.status_code),
                    )

        except Exception as e:
            logger.exception(e)
        return response

    return middleware
