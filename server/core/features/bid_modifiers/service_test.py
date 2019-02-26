import csv
from io import StringIO

import mock
from django.test import TestCase

from dash import constants as dash_constants
from dash import models as dash_models
from dash.features import geolocation
from utils.magic_mixer import magic_mixer

from . import constants
from . import exceptions
from . import helpers
from . import models
from . import service


class TestBidModifierService(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(dash_models.AdGroup)
        self.source = magic_mixer.blend(dash_models.Source, bidder_slug="some_slug")

    def test_get(self):
        service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", self.source, 0.5)
        service.set(self.ad_group, constants.BidModifierType.SOURCE, "test_source", None, 4.6)
        service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, 1.3)
        service.set(self.ad_group, constants.BidModifierType.OPERATING_SYSTEM, "test_operating_system", None, 1.7)
        service.set(self.ad_group, constants.BidModifierType.PLACEMENT, "test_placement", None, 3.6)
        service.set(self.ad_group, constants.BidModifierType.COUNTRY, "test_country", None, 2.9)
        service.set(self.ad_group, constants.BidModifierType.STATE, "test_state", None, 2.4)
        service.set(self.ad_group, constants.BidModifierType.DMA, "test_dma", None, 0.6)
        self.assertEqual(
            service.get(self.ad_group),
            [
                {
                    "type": constants.BidModifierType.PUBLISHER,
                    "target": "test_publisher",
                    "source": self.source,
                    "modifier": 0.5,
                },
                {"type": constants.BidModifierType.SOURCE, "target": "test_source", "source": None, "modifier": 4.6},
                {"type": constants.BidModifierType.DEVICE, "target": "test_device", "source": None, "modifier": 1.3},
                {
                    "type": constants.BidModifierType.OPERATING_SYSTEM,
                    "target": "test_operating_system",
                    "source": None,
                    "modifier": 1.7,
                },
                {
                    "type": constants.BidModifierType.PLACEMENT,
                    "target": "test_placement",
                    "source": None,
                    "modifier": 3.6,
                },
                {"type": constants.BidModifierType.COUNTRY, "target": "test_country", "source": None, "modifier": 2.9},
                {"type": constants.BidModifierType.STATE, "target": "test_state", "source": None, "modifier": 2.4},
                {"type": constants.BidModifierType.DMA, "target": "test_dma", "source": None, "modifier": 0.6},
            ],
        )

    def test_get_include_types(self):
        service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", self.source, 0.5)
        service.set(self.ad_group, constants.BidModifierType.SOURCE, "test_source", None, 4.6)
        service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, 1.3)
        service.set(self.ad_group, constants.BidModifierType.OPERATING_SYSTEM, "test_operating_system", None, 1.7)
        service.set(self.ad_group, constants.BidModifierType.PLACEMENT, "test_placement", None, 3.6)
        service.set(self.ad_group, constants.BidModifierType.COUNTRY, "test_country", None, 2.9)
        service.set(self.ad_group, constants.BidModifierType.STATE, "test_state", None, 2.4)
        service.set(self.ad_group, constants.BidModifierType.DMA, "test_dma", None, 0.6)
        self.assertEqual(
            service.get(self.ad_group, include_types=[constants.BidModifierType.DEVICE, constants.BidModifierType.DMA]),
            [
                {"type": constants.BidModifierType.DEVICE, "target": "test_device", "source": None, "modifier": 1.3},
                {"type": constants.BidModifierType.DMA, "target": "test_dma", "source": None, "modifier": 0.6},
            ],
        )

    def test_get_exclude_types(self):
        service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", self.source, 0.5)
        service.set(self.ad_group, constants.BidModifierType.SOURCE, "test_source", None, 4.6)
        service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, 1.3)
        service.set(self.ad_group, constants.BidModifierType.OPERATING_SYSTEM, "test_operating_system", None, 1.7)
        service.set(self.ad_group, constants.BidModifierType.PLACEMENT, "test_placement", None, 3.6)
        service.set(self.ad_group, constants.BidModifierType.COUNTRY, "test_country", None, 2.9)
        service.set(self.ad_group, constants.BidModifierType.STATE, "test_state", None, 2.4)
        service.set(self.ad_group, constants.BidModifierType.DMA, "test_dma", None, 0.6)
        self.assertEqual(
            service.get(
                self.ad_group,
                exclude_types=[
                    constants.BidModifierType.PUBLISHER,
                    constants.BidModifierType.OPERATING_SYSTEM,
                    constants.BidModifierType.PLACEMENT,
                ],
            ),
            [
                {"type": constants.BidModifierType.SOURCE, "target": "test_source", "source": None, "modifier": 4.6},
                {"type": constants.BidModifierType.DEVICE, "target": "test_device", "source": None, "modifier": 1.3},
                {"type": constants.BidModifierType.COUNTRY, "target": "test_country", "source": None, "modifier": 2.9},
                {"type": constants.BidModifierType.STATE, "target": "test_state", "source": None, "modifier": 2.4},
                {"type": constants.BidModifierType.DMA, "target": "test_dma", "source": None, "modifier": 0.6},
            ],
        )

    def test_set_nonexisting(self):
        self.assertEqual(models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 0)

        service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, 1.2)

        self.assertEqual(models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

        self.assertEqual(
            service.get(self.ad_group),
            [{"type": constants.BidModifierType.DEVICE, "target": "test_device", "source": None, "modifier": 1.2}],
        )

    def test_set_existing(self):
        service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, 0.5)

        self.assertEqual(models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

        service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, 1.2)

        self.assertEqual(models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

        self.assertEqual(
            service.get(self.ad_group),
            [{"type": constants.BidModifierType.DEVICE, "target": "test_device", "source": None, "modifier": 1.2}],
        )

    def test_set_none(self):
        service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, 0.5)

        self.assertEqual(models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 1)

        service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, None)

        self.assertEqual(models.BidModifier.objects.filter(ad_group=self.ad_group).count(), 0)

    def test_set_invalid_type(self):
        with self.assertRaises(exceptions.BidModifierValueInvalid):
            service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, "invalid")

    def test_set_invalid_too_big(self):
        with self.assertRaises(exceptions.BidModifierValueInvalid):
            service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, 35)

    def test_set_invalid_too_small(self):
        with self.assertRaises(exceptions.BidModifierValueInvalid):
            service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", None, -2.0)

    def test_set_invalid_publisher_type(self):
        with self.assertRaises(exceptions.BidModifierSourceInvalid):
            service.set(self.ad_group, constants.BidModifierType.PUBLISHER, "test_publisher", None, 0.5)

    def test_set_invalid_non_publisher_type(self):
        with self.assertRaises(exceptions.BidModifierSourceInvalid):
            service.set(self.ad_group, constants.BidModifierType.DEVICE, "test_device", self.source, 0.5)

    def test_clean_entries(self):
        entries = [
            {
                "Type": constants.BidModifierType.get_text(constants.BidModifierType.PUBLISHER),
                "Target": "all publishers",
                "Source Slug": "some_slug",
                "Bid Modifier": "",
            },
            {
                "Type": constants.BidModifierType.get_text(constants.BidModifierType.PUBLISHER),
                "Target": "example1.com",
                "Source Slug": "some_slug",
                "Bid Modifier": 1.0,
            },
            {
                "Type": constants.BidModifierType.get_text(constants.BidModifierType.PUBLISHER),
                "Target": "example2.com",
                "Source Slug": "some_slug",
                "Bid Modifier": 2.1,
            },
        ]
        test_entries = entries.copy()
        cleaned_entries, has_error = service.clean_entries(entries)
        self.assertFalse(has_error)
        self.assertEqual(
            cleaned_entries,
            [
                {
                    "type": constants.BidModifierType.PUBLISHER,
                    "target": "example1.com",
                    "modifier": None,
                    "source": self.source,
                },
                {
                    "type": constants.BidModifierType.PUBLISHER,
                    "target": "example2.com",
                    "modifier": 2.1,
                    "source": self.source,
                },
            ],
        )
        self.assertEqual(entries, test_entries)

        entries = [
            {
                "Type": helpers.output_modifier_type(constants.BidModifierType.PUBLISHER),
                "Target": "https://example.com",
                "Source Slug": "bad_slug",
                "Bid Modifier": 12.0,
            },
            {
                "Type": helpers.output_modifier_type(constants.BidModifierType.PUBLISHER),
                "Target": "example2.com/",
                "Source Slug": "some_slug",
                "Bid Modifier": 0.0,
            },
            {
                "Type": helpers.output_modifier_type(constants.BidModifierType.PUBLISHER),
                "Target": "example3.com",
                "Source Slug": "some_slug",
                "Bid Modifier": "ASD",
            },
            {
                "Type": helpers.output_modifier_type(constants.BidModifierType.PUBLISHER),
                "Target": "all publishers",
                "Source Slug": "some_slug",
                "Bid Modifier": 2.0,
            },
        ]
        cleaned_entries, has_error = service.clean_entries(entries)
        self.assertEqual(has_error, True)
        self.assertEqual(
            entries[0]["Errors"],
            "Bid modifier too high (> 11.0); Invalid Source Slug; Remove the following prefixes: http, https",
        )
        self.assertEqual(entries[1]["Errors"], "Bid modifier too low (< 0.01); Publisher should not contain /")
        self.assertEqual(entries[2]["Errors"], "Invalid Bid Modifier")
        self.assertEqual(entries[3]["Errors"], "'all publishers' can not have a bid modifier set")

    def test_set_from_cleaned_entries(self):
        cleaned_entries = [
            {
                "type": constants.BidModifierType.PUBLISHER,
                "target": "test_publisher",
                "source": self.source,
                "modifier": 0.5,
            },
            {"type": constants.BidModifierType.SOURCE, "target": "test_source", "source": None, "modifier": 4.6},
            {"type": constants.BidModifierType.DEVICE, "target": "test_device", "source": None, "modifier": 1.3},
            {
                "type": constants.BidModifierType.OPERATING_SYSTEM,
                "target": "test_operating_system",
                "source": None,
                "modifier": 1.7,
            },
            {"type": constants.BidModifierType.PLACEMENT, "target": "test_placement", "source": None, "modifier": 3.6},
            {"type": constants.BidModifierType.COUNTRY, "target": "test_country", "source": None, "modifier": 2.9},
            {"type": constants.BidModifierType.STATE, "target": "test_state", "source": None, "modifier": 2.4},
            {"type": constants.BidModifierType.DMA, "target": "test_dma", "source": None, "modifier": 0.6},
        ]
        service.set_from_cleaned_entries(self.ad_group, cleaned_entries)
        self.assertEqual(
            service.get(self.ad_group),
            [
                {
                    "type": constants.BidModifierType.PUBLISHER,
                    "target": "test_publisher",
                    "source": self.source,
                    "modifier": 0.5,
                },
                {"type": constants.BidModifierType.SOURCE, "target": "test_source", "source": None, "modifier": 4.6},
                {"type": constants.BidModifierType.DEVICE, "target": "test_device", "source": None, "modifier": 1.3},
                {
                    "type": constants.BidModifierType.OPERATING_SYSTEM,
                    "target": "test_operating_system",
                    "source": None,
                    "modifier": 1.7,
                },
                {
                    "type": constants.BidModifierType.PLACEMENT,
                    "target": "test_placement",
                    "source": None,
                    "modifier": 3.6,
                },
                {"type": constants.BidModifierType.COUNTRY, "target": "test_country", "source": None, "modifier": 2.9},
                {"type": constants.BidModifierType.STATE, "target": "test_state", "source": None, "modifier": 2.4},
                {"type": constants.BidModifierType.DMA, "target": "test_dma", "source": None, "modifier": 0.6},
            ],
        )

    def test_make_csv_file(self):
        magic_mixer.blend(dash_models.Source, name="Outbrain", bidder_slug="b1_outbrain")
        magic_mixer.blend(
            geolocation.Geolocation, key="US", type=dash_constants.LocationType.COUNTRY, name="United States"
        )
        magic_mixer.blend(
            geolocation.Geolocation, key="US-TX", type=dash_constants.LocationType.REGION, name="Texas, United States"
        )
        magic_mixer.blend(
            geolocation.Geolocation, key="765", type=dash_constants.LocationType.DMA, name="765 El Paso, TX"
        )

        input_csv_file = service.make_csv_example_file()

        entries = service.parse_csv_file_entries(input_csv_file)
        cleaned_entries, has_error = service.clean_entries(entries)
        self.assertFalse(has_error)

        output_csv_file = service.make_csv_file(cleaned_entries)

        input_csv_file.seek(0)
        self.assertEqual(output_csv_file.read(), input_csv_file.read())

    def test_make_csv_example_file(self):
        outbrain = magic_mixer.blend(dash_models.Source, name="Outbrain", bidder_slug="b1_outbrain")
        magic_mixer.blend(
            geolocation.Geolocation, key="US", type=dash_constants.LocationType.COUNTRY, name="United States"
        )
        magic_mixer.blend(
            geolocation.Geolocation, key="US-TX", type=dash_constants.LocationType.REGION, name="Texas, United States"
        )
        magic_mixer.blend(
            geolocation.Geolocation, key="765", type=dash_constants.LocationType.DMA, name="765 El Paso, TX"
        )

        csv_file = service.make_csv_example_file()
        entries = service.parse_csv_file_entries(csv_file)
        cleaned_entries, has_error = service.clean_entries(entries)
        self.assertFalse(has_error)
        self.assertEqual(
            cleaned_entries,
            [
                {
                    "type": constants.BidModifierType.PUBLISHER,
                    "target": "example.com",
                    "modifier": 1.1,
                    "source": self.source,
                },
                {"type": constants.BidModifierType.SOURCE, "target": str(outbrain.id), "modifier": 1.2, "source": None},
                {
                    "type": constants.BidModifierType.DEVICE,
                    "target": str(dash_constants.DeviceType.MOBILE),
                    "modifier": 1.3,
                    "source": None,
                },
                {
                    "type": constants.BidModifierType.OPERATING_SYSTEM,
                    "target": str(dash_constants.OperatingSystem.ANDROID),
                    "modifier": 1.4,
                    "source": None,
                },
                {
                    "type": constants.BidModifierType.PLACEMENT,
                    "target": str(dash_constants.PlacementMedium.SITE),
                    "modifier": 1.5,
                    "source": None,
                },
                {"type": constants.BidModifierType.COUNTRY, "target": "US", "modifier": 1.6, "source": None},
                {"type": constants.BidModifierType.STATE, "target": "US-TX", "modifier": 1.7, "source": None},
                {"type": constants.BidModifierType.DMA, "target": "765", "modifier": 1.8, "source": None},
            ],
        )

    def test_parse_invalid_bid_modifier_file(self):
        csv_columns = ["Type", "Target", "Illegal", "Bid Modifier"]

        csv_file = StringIO()
        writer = csv.DictWriter(csv_file, csv_columns, extrasaction="ignore")
        writer.writeheader()
        csv_file.seek(0)

        with self.assertRaises(exceptions.InvalidBidModifierFile):
            service.parse_csv_file_entries(csv_file)

    @mock.patch("utils.s3helpers.S3Helper.put")
    def test_make_csv_error_file(self, mock_s3_helper_put):
        csv_columns = ["Type", "Target", "Source Slug", "Bid Modifier"]
        entries = [
            {
                "Type": helpers.output_modifier_type(constants.BidModifierType.PUBLISHER),
                "Target": "example.com",
                "Source Slug": "some_slug",
                "Bid Modifier": "foo",
            },
            {"Type": "invalid", "Target": "Outbrain", "Source Slug": "", "Bid Modifier": "1.2"},
            {
                "Type": helpers.output_modifier_type(constants.BidModifierType.DEVICE),
                "Target": "Illegal",
                "Source Slug": "",
                "Bid Modifier": "1.3",
            },
            {
                "Type": helpers.output_modifier_type(constants.BidModifierType.OPERATING_SYSTEM),
                "Target": "Android",
                "Source Slug": "",
                "Bid Modifier": "30.0",
            },
            {
                "Type": helpers.output_modifier_type(constants.BidModifierType.PLACEMENT),
                "Target": "Website",
                "Source Slug": "",
                "Bid Modifier": "-0.1",
            },
            {
                "Type": helpers.output_modifier_type(constants.BidModifierType.PLACEMENT),
                "Target": "In-app",
                "Source Slug": "",
                "Bid Modifier": "0.5",
            },
            {
                "Type": helpers.output_modifier_type(constants.BidModifierType.COUNTRY),
                "Target": "US",
                "Source Slug": "",
                "Bid Modifier": "1.6",
            },
        ]

        csv_file = StringIO()
        writer = csv.DictWriter(csv_file, csv_columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entries)
        csv_file.seek(0)

        entries = service.parse_csv_file_entries(csv_file)
        cleaned_entries, has_error = service.clean_entries(entries)
        self.assertTrue(has_error)

        service.make_csv_error_file(entries, csv_columns + ["Errors"], self.ad_group.id)

        mock_s3_helper_put.assert_called_once()
        csv_error_content = mock_s3_helper_put.call_args_list[0][0][1]

        error_entires = service.parse_csv_file_entries(StringIO(csv_error_content))

        self.assertEqual(
            error_entires,
            [
                {
                    "Type": helpers.output_modifier_type(constants.BidModifierType.PUBLISHER),
                    "Target": "example.com",
                    "Source Slug": "some_slug",
                    "Bid Modifier": "foo",
                    "Errors": "Invalid Bid Modifier",
                },
                {
                    "Type": "invalid",
                    "Target": "Outbrain",
                    "Source Slug": "",
                    "Bid Modifier": "1.2",
                    "Errors": "Invalid Bid Modifier Type",
                },
                {
                    "Type": helpers.output_modifier_type(constants.BidModifierType.DEVICE),
                    "Target": "Illegal",
                    "Source Slug": "",
                    "Bid Modifier": "1.3",
                    "Errors": "Invalid Device",
                },
                {
                    "Type": helpers.output_modifier_type(constants.BidModifierType.OPERATING_SYSTEM),
                    "Target": "Android",
                    "Source Slug": "",
                    "Bid Modifier": "30.0",
                    "Errors": "Bid modifier too high (> 11.0)",
                },
                {
                    "Type": helpers.output_modifier_type(constants.BidModifierType.PLACEMENT),
                    "Target": "Website",
                    "Source Slug": "",
                    "Bid Modifier": "-0.1",
                    "Errors": "Bid modifier too low (< 0.01)",
                },
                {
                    "Type": helpers.output_modifier_type(constants.BidModifierType.PLACEMENT),
                    "Target": "In-app",
                    "Source Slug": "",
                    "Bid Modifier": "0.5",
                    "Errors": "",
                },
                {
                    "Type": helpers.output_modifier_type(constants.BidModifierType.COUNTRY),
                    "Target": "US",
                    "Source Slug": "",
                    "Bid Modifier": "1.6",
                    "Errors": "Invalid Geolocation",
                },
            ],
        )
