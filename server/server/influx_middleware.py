import re

from django.db import connection
import influx
import logging

logger = logging.getLogger(__name__)


def queries_to_influx(get_response):

    def middleware(request):
        response = get_response(request)

        try:
            total_time = 0

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

            path = re.sub('/[0-9]+/', '/_ID_/', request.path)

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

        except Exception as e:
            logger.exception(e)
        return response

    return middleware
