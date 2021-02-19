from django.http import QueryDict
from djangorestframework_camel_case.util import camel_to_underscore
from rest_framework.parsers import MultiPartParser
from rest_framework.parsers import ParseError
from rest_framework.parsers import six


class CamelCaseJSONMultiPartParser(MultiPartParser):
    """
    Parses multipart HTML form content, which supports file uploads.
    Request data will be underscored and populated with a QueryDict.
    media_type: multipart/form-data
    """

    def parse(self, stream, media_type=None, parser_context=None):
        result = super(CamelCaseJSONMultiPartParser, self).parse(stream, media_type, parser_context)

        try:
            result.data = self._underscoreize(result.data)
        except ValueError as exc:
            raise ParseError("Multipart form parse error - %s" % six.text_type(exc))

        return result

    def _underscoreize(self, data):
        if isinstance(data, QueryDict):
            new_dict = QueryDict(mutable=True, encoding=data.encoding)
            for key, value in data.items():
                new_key = camel_to_underscore(key)
                new_dict[new_key] = self._underscoreize(value)
            new_dict._mutable = False
            return new_dict
        if isinstance(data, dict):
            new_dict = {}
            for key, value in data.items():
                new_key = camel_to_underscore(key)
                new_dict[new_key] = self._underscoreize(value)
            return new_dict
        if isinstance(data, (list, tuple)):
            for i in range(len(data)):
                data[i] = self._underscoreize(data[i])
            return data
        return data
