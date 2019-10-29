import utils.request_context


def trace_id_processor(logger, method_name, event_dict):
    event_dict["trace_id"] = utils.request_context.get("trace_id")
    return event_dict
