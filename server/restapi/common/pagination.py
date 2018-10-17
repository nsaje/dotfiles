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
    - http://example.org/respirce/?limit=100
    - http://example.org/respirce/?marker=100
    - http://example.org/respirce/?marker=400&limit=100

    URLs to be handled by LimitOffsetPagination:
    - http://example.org/respirce/?offset=400
    - http://example.org/respirce/?offset=400&limit=100
    """

    selected_pagination = None

    def paginate_queryset(self, queryset, request, view=None):
        self.selected_pagination = self._select_pagination(request)
        return self.selected_pagination.paginate_queryset(queryset, request, view=view)

    def get_paginated_response(self, data):
        if "data" in data:
            data = data["data"]

        return self.selected_pagination.get_paginated_response(data)

    def _select_pagination(self, request):
        if "offset" in request.query_params:
            return StandardLimitOffsetPagination()

        return MarkerOffsetPagination()


class StandardLimitOffsetPagination(pagination.LimitOffsetPagination):
    """
    Standard LimitOffsetPagination that sets default and maximum page size.
    """

    max_limit = 1000
    default_limit = 100

    def get_paginated_response(self, data):
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

    def paginate_queryset(self, queryset, request, view=None):
        self.limit = self.get_limit(request)
        if self.limit is None:
            return None

        self.marker = self.get_marker(request)
        self.count = self.get_count(queryset)
        self.request = request

        if isinstance(queryset, QuerySet):
            page = queryset.order_by("id")
            if self.marker is not None:
                page = page.filter(id__gt=self.marker)
            page = list(page[: self.limit])

        elif isinstance(queryset, collections.abc.Iterable):

            try:
                page = sorted(queryset, key=lambda x: x.id)
                if self.marker is not None:
                    page = [x for x in page if x.id > self.marker]

                page = page[: self.limit]
            except AttributeError:
                raise ValueError("MarkerOffsetPagination can not handle objects without a primary key")

        else:
            raise ValueError("MarkerOffsetPagination can not handle type {} queryset".format(type(queryset)))

        self.new_marker = page[-1].id if len(page) == self.limit else None
        return page

    def get_paginated_response(self, data):
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
            return queryset.count()
        except (AttributeError, TypeError):
            return len(queryset)
