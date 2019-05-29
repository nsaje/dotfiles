# -*- coding: utf-8 -*-
import copy
import datetime

from django.test import TestCase

from dash import forms
from dash import models
from utils import test_helper
from zemauth.models import User


class BreakdownFormTest(TestCase):
    fixtures = ["test_api.yaml", "test_agency.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=1)

    def test_clean_form(self):
        breakdown = "/account/source/dma/day"
        request_body = {
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "filtered_sources": ["1", "3", "4"],
            "filtered_agencies": ["1", "2"],
            "filtered_account_types": ["1", "3", "2"],
            "show_archived": "true",
            "parents": ["123-7", "23-33", "23-24"],
            "show_blacklisted_publishers": "all",
            "offset": 12,
            "limit": 20,
            "order": "-clicks",
        }

        form = forms.BreakdownForm(breakdown, request_body)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["breakdown"], ["account_id", "source_id", "dma", "day"])
        self.assertEqual(form.cleaned_data["start_date"], datetime.date(2016, 1, 1))
        self.assertEqual(form.cleaned_data["end_date"], datetime.date(2016, 2, 3))
        self.assertEqual(
            form.cleaned_data["filtered_sources"],
            test_helper.QuerySetMatcher(models.Source.objects.filter(pk__in=[1, 3, 4])),
        )
        self.assertEqual(
            form.cleaned_data["filtered_agencies"], test_helper.QuerySetMatcher(models.Agency.objects.filter(pk=1))
        )
        self.assertEqual(form.cleaned_data["filtered_account_types"], test_helper.ListMatcher([1, 3, 2]))
        self.assertEqual(form.cleaned_data["show_archived"], True)
        self.assertEqual(form.cleaned_data["parents"], ["123-7", "23-33", "23-24"])
        self.assertEqual(form.cleaned_data["offset"], 12)
        self.assertEqual(form.cleaned_data["limit"], 20)
        self.assertEqual(form.cleaned_data["order"], "-clicks")
        self.assertEqual(form.cleaned_data["show_blacklisted_publishers"], "all")

    def test_funky_parents(self):
        request_body = {
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "limit": 10,
            "offset": 20,
            "parents": [None],
        }

        form = forms.BreakdownForm("/account", copy.copy(request_body))
        self.assertTrue(form.is_valid())
        self.assertEqual([], form.cleaned_data["parents"])

        request_body = {
            "start_date": "2016-01-01",
            "end_date": "2016-02-03",
            "limit": 10,
            "offset": 20,
            "parents": [None, "mekani ć", 1],
        }

        form = forms.BreakdownForm("/account", copy.copy(request_body))
        self.assertTrue(form.is_valid())
        self.assertEqual(["mekani ć", "1"], form.cleaned_data["parents"])

    def test_required_fields(self):
        form = forms.BreakdownForm("", {})

        self.assertFalse(form.is_valid())

        self.assertIn("start_date", form.errors)
        self.assertIn("end_date", form.errors)
        self.assertIn("offset", form.errors)
        self.assertIn("limit", form.errors)
        self.assertIn("breakdown", form.errors)

        self.assertNotIn("show_archived", form.errors)
        self.assertNotIn("parents", form.errors)
        self.assertNotIn("filtered_sources", form.errors)
        self.assertNotIn("order", form.errors)

    def test_clean_breakdown(self):
        request_body = {"start_date": "2016-01-01", "end_date": "2016-02-03", "limit": 10, "offset": 20}

        form = forms.BreakdownForm("/account/source/dma/day", copy.copy(request_body))
        self.assertTrue(form.is_valid())

        self.assertEqual(["account_id", "source_id", "dma", "day"], form.cleaned_data["breakdown"])

        form = forms.BreakdownForm("/account/", copy.copy(request_body))
        self.assertTrue(form.is_valid())

        self.assertEqual(["account_id"], form.cleaned_data["breakdown"])

        form = forms.BreakdownForm("/account/asd/", copy.copy(request_body))
        self.assertTrue(form.is_valid())

        self.assertEqual(["account_id", "asd"], form.cleaned_data["breakdown"])

        form = forms.BreakdownForm("", copy.copy(request_body))
        self.assertFalse(form.is_valid(), "Breakdown path should be specified")
