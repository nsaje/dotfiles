import collections

from django.db.models.query import QuerySet
from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class StandardPagination(pagination.BasePagination):
    """
    Pagination proxy that uses MarkerOffsetPagination by default
    or LimitOffsetPagination when using "offset" URL parameter.

    URLs to be handled by MarkerOffsetPagination:
    - http://example.org/resource/?limit=100
    - http://example.org/resource/?marker=100
    - http://example.org/resource/?marker=400&limit=100

    URLs to be handled by LimitOffsetPagination:
    - http://example.org/resource/?offset=400
    - http://example.org/resource/?offset=400&limit=100
    """

    selected_pagination = None
    max_limit = None
    default_limit = None

    def __init__(self, max_limit=None, default_limit=None):
        self.max_limit = max_limit
        self.default_limit = default_limit

    def paginate_queryset(self, queryset, request, view=None):
        self.selected_pagination = self._select_pagination(request)
        return self.selected_pagination.paginate_queryset(queryset, request, view=view)

    def get_paginated_response(self, data):
        return self.selected_pagination.get_paginated_response(data)

    def _select_pagination(self, request):
        if "offset" in request.query_params:
            return StandardLimitOffsetPagination(max_limit=self.max_limit, default_limit=self.default_limit)

        return MarkerOffsetPagination(max_limit=self.max_limit, default_limit=self.default_limit)


class StandardLimitOffsetPagination(pagination.LimitOffsetPagination):
    """
    Standard LimitOffsetPagination that sets default and maximum page size.
    """

    max_limit = 1000
    default_limit = 100

    def __init__(self, max_limit=None, default_limit=None):
        self.max_limit = max_limit or self.max_limit
        self.default_limit = default_limit or self.default_limit

    def get_paginated_response(self, data):
        if "data" in data:
            data = data["data"]

        return Response(
            collections.OrderedDict(
                [
                    ("count", self.count),
                    ("next", self.get_next_link()),
                    ("previous", self.get_previous_link()),
                    ("data", data),
                ]
            )
        )


class MarkerOffsetPagination(pagination.BasePagination):
    """
    Marker offset pagination that uses object primary key as offset.
    """

    max_limit = 1000
    default_limit = 100
    limit_query_param = "limit"
    marker_query_param = "marker"

    def __init__(self, max_limit=None, default_limit=None):
        self.max_limit = max_limit or self.max_limit
        self.default_limit = default_limit or self.default_limit

    def paginate_queryset(self, queryset, request, view=None):
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.marker = self.get_marker(request)
        self.count = self.get_count(queryset)
        self.request = request

        try:
            if isinstance(queryset, QuerySet):
                page = queryset.order_by("id")
                if self.marker is not None:
                    page = page.filter(id__gt=self.marker)
                page = list(page[: self.limit])

            elif isinstance(queryset, collections.abc.Iterable):
                page = sorted(queryset, key=lambda x: _extract_id(x))
                if self.marker is not None:
                    page = [x for x in page if _extract_id(x) > self.marker]

                page = page[: self.limit]

            else:
                raise ValueError("MarkerOffsetPagination can not handle type {} queryset".format(type(queryset)))

            self.new_marker = _extract_id(page[-1]) if len(page) == self.limit else None

        except AttributeError:
            raise ValueError("MarkerOffsetPagination can not handle objects without a primary key")

        return page

    def get_paginated_response(self, data):
        if "data" in data:
            data = data["data"]

        return Response(
            collections.OrderedDict([("count", self.count), ("next", self.get_next_link()), ("data", data)])
        )

    def get_limit(self, request):
        if self.limit_query_param:
            try:
                return pagination._positive_int(
                    request.query_params[self.limit_query_param], strict=True, cutoff=self.max_limit
                )
            except (KeyError, ValueError):
                pass

        return self.default_limit

    def get_marker(self, request):
        try:
            return pagination._positive_int(request.query_params[self.marker_query_param])
        except (KeyError, ValueError):
            return None

    def get_next_link(self):
        if self.new_marker is None:
            return None

        url = self.request.build_absolute_uri()
        url = replace_query_param(url, self.limit_query_param, self.limit)

        return replace_query_param(url, self.marker_query_param, self.new_marker)

    def get_count(self, queryset):
        """
        Determine an object count, supporting either querysets or regular lists.
        """
        try:
            if hasattr(queryset, "cached_count"):
                return queryset.cached_count()
            return queryset.count()
        except (AttributeError, TypeError):
            return len(queryset)


def _extract_id(obj):
    if isinstance(obj, collections.abc.Mapping):
        if "id" in obj or "pk" in obj:
            return obj.get("id") or obj.get("pk")

        raise ValueError(f"Can not extract primary key from {obj}")

    return obj.id
