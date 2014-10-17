from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def paginate(result, page, page_size):
    paginator = Paginator(result, page_size)

    try:
        result_pg = paginator.page(page)
    except PageNotAnInteger:
        result_pg = paginator.page(1)
    except EmptyPage:
        result_pg = paginator.page(paginator.num_pages)

    return (
        [r for r in result_pg],
        result_pg.number,
        result_pg.paginator.num_pages,
        result_pg.paginator.count,
        result_pg.start_index(),
        result_pg.end_index()
    )
