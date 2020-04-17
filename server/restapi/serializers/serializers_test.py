from django.http.request import QueryDict
from django.test import TestCase
from rest_framework import fields

from .serializers import QueryParamsExpectations


class QueryParamsExpectationsTest(QueryParamsExpectations):
    strv = fields.CharField(required=False)
    listv = fields.ListField(child=fields.CharField(), required=False)
    choicev = fields.ListField(child=fields.ChoiceField(choices=["a", "b"]), required=False)
    multiple_words = fields.IntegerField(required=False)


class QueryParamsExpectationsTestCase(TestCase):
    def test_comma_handling(self):
        query = QueryDict("strv=a,b&listv=a,b&choicev=a,b")
        serializer = QueryParamsExpectationsTest(data=query)
        serializer.is_valid(raise_exception=True)

        self.assertEqual(serializer.validated_data["strv"], "a,b")
        self.assertEqual(serializer.validated_data["listv"], ["a", "b"])
        self.assertEqual(serializer.validated_data["choicev"], ["a", "b"])

    def test_case_convert(self):
        query = QueryDict("multipleWords=123")
        serializer = QueryParamsExpectationsTest(data=query)
        serializer.is_valid(raise_exception=True)

        self.assertEqual(serializer.validated_data["multiple_words"], 123)
        self.assertNotIn("multipleWords", serializer.validated_data)

    def test_not_supported_param(self):
        query = QueryDict("debug=a")
        serializer = QueryParamsExpectationsTest(data=query)
        serializer.is_valid(raise_exception=True)
        self.assertEqual(serializer.validated_data.get("debug"), None)
