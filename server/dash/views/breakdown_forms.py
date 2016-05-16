import json

from utils import exc

from dash.views import helpers

from stats import constants

DEFAULT_PAGE = 1
DEFAULT_PAGE_SIZE = 10


def clean_default_params(user, request_data):
    start_date = helpers.get_stats_start_date(request_data.get('start_date'))
    end_date = helpers.get_stats_end_date(request_data.get('end_date'))
    print request_data.get('filtered_sources')
    filtered_sources = helpers.get_filtered_sources(
        user, request_data.get('filtered_sources'))
    show_archived = request_data.get('show_archived') == 'true'
    return {
        'date__gte': start_date,
        'date__lte': end_date,
        'source': filtered_sources,
        'show_archived': show_archived,
    }


def clean_breakdown(breakdown):
    return [x for x in breakdown.split('/') if x]


def clean_page_params(request_data):
    page = int(request_data.get('page')) if request_data.get('page') else DEFAULT_PAGE
    page_size = int(request_data.get('size')) if request_data.get('size') else DEFAULT_PAGE_SIZE

    return page, page_size


def clean_breakdown_page(request_data, breakdown):
    breakdown_page = request_data.get('breakdown_page')
    if not breakdown_page:
        return None

    return _clean_breakdown_page(json.loads(breakdown_page), breakdown, 0)


def _clean_breakdown_page(page, breakdown, dimension_idx):
    dimension = breakdown[dimension_idx]

    if isinstance(page, dict):
        branches = []
        for k, subpage in page.items():
            subbranches = _clean_breakdown_page(subpage, breakdown,
                                                dimension_idx + 1)
            if dimension in constants.IntegerDimensions:
                k = int(k)

            for branch in subbranches:
                branch.update({dimension: k, })

            branches.extend(subbranches)
        return branches

    if dimension in constants.IntegerDimensions:
        page = [int(x) for x in page]

    return [{dimension: page}]


def clean_order(request_data):
    return request_data.get('order')
