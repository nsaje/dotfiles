import uuid

import utils.request_context


def trace_id_middleware(get_response):
    def middleware(request):
        trace_id = request.META.get("HTTP_X_AMZN_TRACE_ID") or uuid.uuid1()
        utils.request_context.set("trace_id", trace_id)
        response = get_response(request)
        response["X_Z1_TRACE_ID"] = trace_id
        return response

    return middleware
