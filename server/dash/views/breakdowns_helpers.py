import json
from utils import exc
from dash import constants
from dash.views import helpers


STRUCTURE = ['account', 'campaign', 'ad_group', 'content_ad', 'source', 'publisher']
STRUCTURE_IDS = ['account', 'campaign', 'ad_group', 'content_ad', 'source']


def clean_default_params(request):
    # TODO use a form for this?
    # TODO validate data is correct
    request_data = request.GET
    if request.method == "POST":
        request_data = request.POST

    start_date = helpers.get_stats_start_date(request_data.get('start_date'))
    end_date = helpers.get_stats_end_date(request_data.get('end_date'))
    filtered_sources = helpers.get_filtered_sources(request.user, request_data.get('filtered_sources'))
    show_archived = request_data.get('show_archived') == 'true'

    return {
        'start_date': start_date,
        'end_date': end_date,
        'filtered_sources': filtered_sources,
        'show_archived': show_archived,
    }


def clean_breakdown(request, base_view, breakdown):
    # TODO check:
    # is valid order
    # is valid breakdown (correct selectors)
    # check level -> base -> structure
    if len(breakdown) > 4:
        raise exc.InvalidBreakdownError('More than 4 dimensions')

    return breakdown


def clean_page_params(request):
    # TODO this needs to be generalized or passed in as a parameter
    request_data = request.GET
    if request.method == "POST":
        request_data = request.POST

    page = int(request_data.get('page'))  # 1, 2, 3, ...
    page_size = int(request_data.get('page_size'))  # for the shown level 5, 10, 20, 60 ...

    return page, page_size


def clean_breakdown_page(request, breakdown):
    request_data = request.GET
    if request.method == "POST":
        request_data = request.POST

    breakdown_page = None
    if len(breakdown) > 1:
        breakdown_page = json.loads(request_data.get('breakdown_page'))
        breakdown_page = _clean_breakdown_page(breakdown_page, breakdown, 0)

    return breakdown_page


def _clean_breakdown_page(page, breakdown, dimension_idx):
    dimension = breakdown[dimension_idx]
    if isinstance(page, dict):
        new_page = {}
        for k, v in page.items():
            if dimension in STRUCTURE_IDS:
                k = int(k)
            new_page[k] = _clean_breakdown_page(v, breakdown, dimension_idx + 1)
        return new_page

    if dimension in STRUCTURE_IDS:
        return [int(x) for x in page]
    return page


def clean_order(request):
    return request.GET.get('order')
