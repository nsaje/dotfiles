from django.conf import settings
from django.db import connections

import structlog
from utils import influx_helper
from utils import metrics_compat

logger = structlog.get_logger(__name__)

DATABASE_NAMES = ["default"] + settings.DATABASE_READ_REPLICAS


def queries_to_influx(get_response):
    def middleware(request):
        for name in DATABASE_NAMES:
            connections[name].force_debug_cursor = True

        response = get_response(request)

        try:
            total_time = 0
            total_queries = 0
            queries_per_verb = {"SELECT": 0, "INSERT": 0, "UPDATE": 0, "DELETE": 0, "OTHER": 0}

            for name in DATABASE_NAMES:
                total_queries += len(connections[name].queries)
                for query in connections[name].queries:
                    query_time = query.get("time")
                    if query_time is None:
                        # django-debug-toolbar monkeypatches the connection
                        # cursor wrapper and adds extra information in each
                        # item in connection.queries. The query time is stored
                        # under the key "duration" rather than "time" and is
                        # in milliseconds, not seconds.
                        query_time = query.get("duration", 0) / 1000
                    total_time += float(query_time)
                    try:
                        queries_per_verb[query["sql"][:6]] += 1
                    except KeyError:
                        queries_per_verb["OTHER"] += 1

            path = influx_helper.clean_path(request.path)

            if total_queries > 0:
                metrics_compat.timing(
                    "queries.timer", total_time, path=path, method=request.method, status=str(response.status_code)
                )
                metrics_compat.timing(
                    "queries.count",
                    total_queries,
                    verb=None,
                    path=path,
                    method=request.method,
                    status=str(response.status_code),
                )
                for verb, count in list(queries_per_verb.items()):
                    metrics_compat.timing(
                        "queries.count",
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
