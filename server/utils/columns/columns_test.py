import datetime

import mock
from django.test import TestCase

import dash.models

from . import columns
from . import exceptions


class FieldNamesTest(TestCase):
    def test_field_names(self):
        self.assertEqual(columns.FieldNames.account_status, "account_status")
        self.assertEqual(columns.FieldNames.domain_link, "domain_link")
        self.assertEqual(columns.FieldNames.avg_etfm_cost_per_new_visitor, "avg_etfm_cost_per_new_visitor")


@mock.patch("utils.dates_helper.local_today", lambda: datetime.date(2017, 8, 8))
class AddDateToName(TestCase):
    def test_add_date_to_name(self):
        self.assertEqual(columns.add_date_to_name("Bla"), "Bla (2017-08-08)")


class NameMappingTest(TestCase):
    def test_get_column_name(self):
        mapping = columns.custom_field_to_column_name_mapping()
        self.assertEqual(columns.get_column_name("unique_users", mapping), "Unique Users")
        self.assertEqual(columns.get_column_name("publisher", mapping), "Publisher")

        with self.assertRaises(exceptions.ColumnNameNotFound):
            columns.get_column_name("", mapping)

    def test_get_field_name(self):
        mapping = columns.custom_column_to_field_name_mapping()
        self.assertEqual(columns.get_field_name("Unique Users", mapping), "unique_users")
        self.assertEqual(columns.get_field_name("Publisher", mapping), "publisher")

        with self.assertRaises(exceptions.FieldNameNotFound):
            columns.get_field_name("", mapping)


class ColumnNamesTest(TestCase):
    fixtures = ["test_augmenter.yaml"]

    def test_get_pixel_field_names_mapping(self):
        self.assertDictEqual(
            columns._get_pixel_field_names_mapping(dash.models.ConversionPixel.objects.all()),
            {
                "Test 1 day": "pixel_1_24",
                "Conversion rate (Test 1 day)": "conversion_rate_per_pixel_1_24",
                "CPA (Test 1 day)": "avg_etfm_cost_per_pixel_1_24",
                "ROAS (Test 1 day)": "etfm_roas_pixel_1_24",
                "Test 1 day - Click attr.": "pixel_1_24",
                "Conversion rate (Test 1 day - Click attr.)": "conversion_rate_per_pixel_1_24",
                "CPA (Test 1 day - Click attr.)": "avg_etfm_cost_per_pixel_1_24",
                "ROAS (Test 1 day - Click attr.)": "etfm_roas_pixel_1_24",
                "Test 7 days": "pixel_1_168",
                "Conversion rate (Test 7 days)": "conversion_rate_per_pixel_1_168",
                "CPA (Test 7 days)": "avg_etfm_cost_per_pixel_1_168",
                "ROAS (Test 7 days)": "etfm_roas_pixel_1_168",
                "Test 7 days - Click attr.": "pixel_1_168",
                "Conversion rate (Test 7 days - Click attr.)": "conversion_rate_per_pixel_1_168",
                "CPA (Test 7 days - Click attr.)": "avg_etfm_cost_per_pixel_1_168",
                "ROAS (Test 7 days - Click attr.)": "etfm_roas_pixel_1_168",
                "Test 30 days": "pixel_1_720",
                "Conversion rate (Test 30 days)": "conversion_rate_per_pixel_1_720",
                "CPA (Test 30 days)": "avg_etfm_cost_per_pixel_1_720",
                "ROAS (Test 30 days)": "etfm_roas_pixel_1_720",
                "Test 30 days - Click attr.": "pixel_1_720",
                "Conversion rate (Test 30 days - Click attr.)": "conversion_rate_per_pixel_1_720",
                "CPA (Test 30 days - Click attr.)": "avg_etfm_cost_per_pixel_1_720",
                "ROAS (Test 30 days - Click attr.)": "etfm_roas_pixel_1_720",
                "Test 90 days": "pixel_1_2160",
                "Conversion rate (Test 90 days)": "conversion_rate_per_pixel_1_2160",
                "CPA (Test 90 days)": "avg_etfm_cost_per_pixel_1_2160",
                "ROAS (Test 90 days)": "etfm_roas_pixel_1_2160",
                "Test 90 days - Click attr.": "pixel_1_2160",
                "Conversion rate (Test 90 days - Click attr.)": "conversion_rate_per_pixel_1_2160",
                "CPA (Test 90 days - Click attr.)": "avg_etfm_cost_per_pixel_1_2160",
                "ROAS (Test 90 days - Click attr.)": "etfm_roas_pixel_1_2160",
                "Test 1 day - View attr.": "pixel_1_24_view",
                "Conversion rate (Test 1 day - View attr.)": "conversion_rate_per_pixel_1_24_view",
                "CPA (Test 1 day - View attr.)": "avg_etfm_cost_per_pixel_1_24_view",
                "ROAS (Test 1 day - View attr.)": "etfm_roas_pixel_1_24_view",
                "Test 7 days - View attr.": "pixel_1_168_view",
                "Conversion rate (Test 7 days - View attr.)": "conversion_rate_per_pixel_1_168_view",
                "CPA (Test 7 days - View attr.)": "avg_etfm_cost_per_pixel_1_168_view",
                "ROAS (Test 7 days - View attr.)": "etfm_roas_pixel_1_168_view",
                "Test 30 days - View attr.": "pixel_1_720_view",
                "Conversion rate (Test 30 days - View attr.)": "conversion_rate_per_pixel_1_720_view",
                "CPA (Test 30 days - View attr.)": "avg_etfm_cost_per_pixel_1_720_view",
                "ROAS (Test 30 days - View attr.)": "etfm_roas_pixel_1_720_view",
            },
        )

    def test_get_conversion_goals_field_names_mapping(self):
        self.assertDictEqual(
            columns._get_conversion_goals_field_names_mapping(dash.models.ConversionGoal.objects.all()),
            {
                "test conversion goal 2": "conversion_goal_2",
                "Conversion rate (test conversion goal 2)": "conversion_rate_per_conversion_goal_2",
                "CPA (test conversion goal 2)": "avg_etfm_cost_per_conversion_goal_2",
                "test conversion goal 3": "conversion_goal_3",
                "Conversion rate (test conversion goal 3)": "conversion_rate_per_conversion_goal_3",
                "CPA (test conversion goal 3)": "avg_etfm_cost_per_conversion_goal_3",
                "test conversion goal 4": "conversion_goal_4",
                "Conversion rate (test conversion goal 4)": "conversion_rate_per_conversion_goal_4",
                "CPA (test conversion goal 4)": "avg_etfm_cost_per_conversion_goal_4",
                "test conversion goal 5": "conversion_goal_5",
                "Conversion rate (test conversion goal 5)": "conversion_rate_per_conversion_goal_5",
                "CPA (test conversion goal 5)": "avg_etfm_cost_per_conversion_goal_5",
            },
        )
