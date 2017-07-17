import logging

logger = logging.getLogger('zem.request')

log_format_started = "STARTED {method} {full_path} elb={elb} traefik={traefik}"


def zem_logging_middleware(get_response):

    def middleware(request):
        elb = request.META.get('HTTP_X_AMZN_TRACE_ID', '-')
        traefik = request.META.get('HTTP_X_TRAEFIK_REQID', '-')
        logger.info(
            log_format_started.format(
                method=request.method,
                full_path=request.get_full_path(),
                elb=elb,
                traefik=traefik
            )
        )
        response = get_response(request)
        return response

    return middleware
