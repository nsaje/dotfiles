import collections

from rest_framework import pagination
from rest_framework.response import Response


class StandardPagination(pagination.LimitOffsetPagination):
    max_limit = 1000
    default_limit = 100

    def get_paginated_response(self, data):
        if 'data' in data:
            data = data['data']

        return Response(collections.OrderedDict([
            ('count', self.count),
            ('next', self.get_next_link()),
            ('previous', self.get_previous_link()),
            ('data', data)
        ]))
