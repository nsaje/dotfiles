from django import forms
from django.test import TestCase
from rest_framework import serializers

from dash import compatibility


class RestFrameworkFieldTest(TestCase):
    class FooBarForm(forms.Form):
        foo = compatibility.forms.RestFrameworkField(serializers.CharField(max_length=3), required=True)

    def test_rest_field(self):
        f = self.FooBarForm({"foo": "bar"})
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data, {"foo": "bar"})

    def test_rest_field_required(self):
        f = self.FooBarForm({"foo": ""})
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors["foo"], ["This field may not be blank."])

    def test_rest_field_length(self):
        f = self.FooBarForm({"foo": "1234"})
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors["foo"], ["Ensure this field has no more than 3 characters."])


class BarSerializer(serializers.Serializer):
    bar_name = serializers.CharField(max_length=3)


class FooSerializer(serializers.Serializer):
    foo_name = serializers.CharField(max_length=3, required=False)
    bar_many = BarSerializer(many=True, required=False)
    bar_one = BarSerializer()


class RestFrameworkSerializerTest(TestCase):
    class FooBarForm(forms.Form):
        foo = compatibility.forms.RestFrameworkSerializer(FooSerializer)

    def test_rest_serializer(self):
        f = self.FooBarForm(
            {
                "foo": {
                    "foo_name": "dog",
                    "bar_many": [{"bar_name": "dog"}, {"bar_name": "cat"}],
                    "bar_one": {"bar_name": "bee"},
                }
            }
        )
        self.assertTrue(f.is_valid())
        self.assertEqual(
            f.cleaned_data,
            {
                "foo": {
                    "foo_name": "dog",
                    "bar_many": [{"bar_name": "dog"}, {"bar_name": "cat"}],
                    "bar_one": {"bar_name": "bee"},
                }
            },
        )

    def test_rest_serializer_required(self):
        f = self.FooBarForm({})
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors["foo"], ["This field is required."])

    def test_rest_serializer_blank(self):
        f = self.FooBarForm({"foo": {}})
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors["foo"], ["This field is required."])

    def test_rest_field_validation(self):
        f = self.FooBarForm({"foo": {"bar_one": {"bar_name": "asdf"}}})
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors["foo"], ['{"bar_one": {"bar_name": ["Ensure this field has no more than 3 characters."]}}']
        )
