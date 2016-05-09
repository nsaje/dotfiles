from dash.views import helpers


def clean_default_parameters(request):
    start_date = helpers.get_stats_start_date(request.GET.get('start_date'))
    end_date = helpers.get_stats_end_date(request.GET.get('end_date'))
    filtered_sources = helpers.get_filtered_sources(request.user, request.GET.get('filtered_sources'))
    show_archived = request.GET.get('show_archived') == 'true'

    return {
        'start_date': start_date,
        'end_date': end_date,
        'filtered_sources': filtered_sources,
        'show_archived': show_archived,
    }


def clean_breakdown(request, params):
    pass


def clean_order(request):
    return request.GET.get('order')
