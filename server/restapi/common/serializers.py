from rest_framework import serializers
from djangorestframework_camel_case.util import camel_to_underscore
from django.http.request import QueryDict

import utils.list_helper


class QueryParamsExpectations(serializers.Serializer):

    def __init__(self, *args, **kwargs):
        data = kwargs.pop('data')
        assert type(data) == QueryDict, "QueryParamsExpectations should only be used for query parameters validation!"
        kwargs['data'] = QueryDict()
        if data:
            snake_cased_data = QueryDict(mutable=True)
            for key in data:
                snake_cased_key = camel_to_underscore(key)
                value = data.getlist(key)
                if hasattr(value, '__iter__'):
                    value = utils.list_helper.flatten(x.split(',') for x in value)
                snake_cased_data.setlist(snake_cased_key, value)
            kwargs['data'] = snake_cased_data
        super(QueryParamsExpectations, self).__init__(*args, **kwargs)
