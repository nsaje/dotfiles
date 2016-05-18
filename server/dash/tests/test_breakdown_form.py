import copy
import datetime
import json

from django.test import TestCase

from zemauth.models import User

from dash import models
from dash import forms

from utils import test_helper


class BreakdownFormTest(TestCase):
    fixtures = ['test_api.yaml']

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def test_clean_form(self):
        breakdown = '/account/source/dma/day'
        request_body = {
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'filtered_sources': '1,3,4',
            'show_archived': 'true',
            'breakdown_page': ['123-7', '23-33', '23-24'],
            'offset': 12,
            'limit': 20,
            'order': '-clicks',
        }

        form = forms.BreakdownForm(self.user, breakdown, request_body)

        self.assertTrue(form.is_valid())
        self.assertDictEqual(form.cleaned_data, {
            'breakdown': ['account', 'source', 'dma', 'day'],
            'start_date': datetime.date(2016, 1, 1),
            'end_date': datetime.date(2016, 2, 3),
            'filtered_sources': test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
            'show_archived': True,
            'breakdown_page': ['123-7', '23-33', '23-24'],
            'offset': 12,
            'limit': 20,
            'order': '-clicks',
        })


    def test_required_fields(self):
        form = forms.BreakdownForm(self.user, '', {})

        self.assertFalse(form.is_valid())

        self.assertIn('start_date', form.errors)
        self.assertIn('end_date', form.errors)
        self.assertIn('offset', form.errors)
        self.assertIn('limit', form.errors)
        self.assertIn('breakdown', form.errors)

        self.assertNotIn('show_archived', form.errors)
        self.assertNotIn('breakdown_page', form.errors)
        self.assertNotIn('filtered_sources', form.errors)
        self.assertNotIn('order', form.errors)

    def test_clean_breakdown(self):
        request_body = {
            'start_date': '2016-01-01',
            'end_date': '2016-02-03',
            'limit': 10,
            'offset': 20,
        }

        form = forms.BreakdownForm(self.user, '/account/source/dma/day', copy.copy(request_body))
        self.assertTrue(form.is_valid())

        self.assertEqual(
            ['account', 'source', 'dma', 'day'],
            form.cleaned_data['breakdown']
        )

        form = forms.BreakdownForm(self.user, '/account/asd/', copy.copy(request_body))
        self.assertTrue(form.is_valid())

        self.assertEqual(
            ['account', 'asd'],
            form.cleaned_data['breakdown']
        )

        form = forms.BreakdownForm(self.user, '', copy.copy(request_body))
        self.assertFalse(form.is_valid(), 'Breakdown path should be specified')
