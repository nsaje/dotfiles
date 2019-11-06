import logging

import utils.request_context


class TraceIdFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = utils.request_context.get("trace_id")
        return True
