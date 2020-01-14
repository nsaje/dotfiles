import csv
import io
from tempfile import NamedTemporaryFile

import mock
from django.urls import reverse

import core.models
import restapi.common.views_base_test
from core.features import bid_modifiers
from dash import constants
from dash.features import geolocation
from utils import test_helper
from utils.magic_mixer import magic_mixer


class BidModifierCSVTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        super(BidModifierCSVTest, self).setUp()
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__users=[self.user])
        self.source = magic_mixer.blend(core.models.Source, bidder_slug="source_slug")

        self.outbrain = magic_mixer.blend(core.models.Source, name="Outbrain", bidder_slug="b1_outbrain")
        self.outbrain_source = magic_mixer.blend(
            core.models.AdGroupSource, ad_group=self.ad_group, source=self.outbrain
        )
        self.us = magic_mixer.blend(
            geolocation.Geolocation, key="US", type=constants.LocationType.COUNTRY, name="United States"
        )
        self.tx = magic_mixer.blend(
            geolocation.Geolocation, key="US-TX", type=constants.LocationType.REGION, name="Texas, United States"
        )
        self.ep = magic_mixer.blend(
            geolocation.Geolocation, key="765", type=constants.LocationType.DMA, name="765 El Paso, TX"
        )
        self.ad = magic_mixer.blend(core.models.ContentAd)

    def test_upload_and_download_modifiers(self):
        csv_file = NamedTemporaryFile(mode="w+", suffix=".csv")
        target_column_name = bid_modifiers.helpers.output_modifier_type(
            bid_modifiers.constants.BidModifierType.PUBLISHER
        )
        csv_columns = [target_column_name, "Source Slug", "Bid Modifier"]
        entries = [{target_column_name: "example.com", "Source Slug": self.source.bidder_slug, "Bid Modifier": "1.2"}]

        csv_writer = csv.DictWriter(csv_file, csv_columns)
        csv_writer.writeheader()
        csv_writer.writerows(entries)
        csv_file.seek(0)

        response = self.client.post(
            reverse(
                "bid_modifiers_upload",
                kwargs={
                    "ad_group_id": self.ad_group.id,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    ),
                },
            ),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "deleted": {"count": 0, "dimensions": 0, "summary": []},
                    "created": {"count": 1, "dimensions": 1, "summary": [{"type": "PUBLISHER", "count": 1}]},
                }
            },
        )

        updated_modifiers = bid_modifiers.service.get(self.ad_group)
        self.assertEqual(len(updated_modifiers), 1)  # Only 6, since "1.0" and "" are ignored.

        self.assertEqual(
            bid_modifiers.service.get(self.ad_group),
            [
                {
                    "type": bid_modifiers.constants.BidModifierType.PUBLISHER,
                    "target": "example.com",
                    "source": self.source,
                    "modifier": 1.2,
                }
            ],
        )

        response = self.client.get(
            reverse(
                "bid_modifiers_download",
                kwargs={
                    "ad_group_id": self.ad_group.id,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    ),
                },
            )
        )
        self.assertEqual(response.status_code, 200)

        csv_reader = csv.DictReader(io.StringIO(response.content.decode("utf8")))

        self.assertEqual([row for row in csv_reader], entries)  # The last two entries were ignored.

    def test_upload_and_download_modifiers_equal_to_one(self):
        csv_file = NamedTemporaryFile(mode="w+", suffix=".csv")
        target_column_name = bid_modifiers.helpers.output_modifier_type(
            bid_modifiers.constants.BidModifierType.PUBLISHER
        )
        csv_columns = [target_column_name, "Source Slug", "Bid Modifier"]
        entries = [{target_column_name: "example.com", "Source Slug": self.source.bidder_slug, "Bid Modifier": "1.0"}]

        csv_writer = csv.DictWriter(csv_file, csv_columns)
        csv_writer.writeheader()
        csv_writer.writerows(entries)
        csv_file.seek(0)

        response = self.client.post(
            reverse(
                "bid_modifiers_upload",
                kwargs={
                    "ad_group_id": self.ad_group.id,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    ),
                },
            ),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "deleted": {"count": 0, "dimensions": 0, "summary": []},
                    "created": {"count": 0, "dimensions": 0, "summary": []},
                }
            },
        )

        updated_modifiers = bid_modifiers.service.get(self.ad_group)
        self.assertEqual(len(updated_modifiers), 0)

        self.assertEqual(bid_modifiers.service.get(self.ad_group), [])

        response = self.client.get(
            reverse(
                "bid_modifiers_download",
                kwargs={
                    "ad_group_id": self.ad_group.id,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    ),
                },
            )
        )
        self.assertEqual(response.status_code, 200)

        csv_reader = csv.DictReader(io.StringIO(response.content.decode("utf8")))

        self.assertEqual([row for row in csv_reader], [])

    def test_validate_upload_modifiers(self):
        csv_file = NamedTemporaryFile(mode="w+", suffix=".csv")
        target_column_name = bid_modifiers.helpers.output_modifier_type(
            bid_modifiers.constants.BidModifierType.PUBLISHER
        )
        csv_columns = [target_column_name, "Source Slug", "Bid Modifier"]
        entries = [{target_column_name: "example.com", "Source Slug": self.source.bidder_slug, "Bid Modifier": "1.2"}]

        csv_writer = csv.DictWriter(csv_file, csv_columns)
        csv_writer.writeheader()
        csv_writer.writerows(entries)
        csv_file.seek(0)

        response = self.client.post(
            reverse(
                "bid_modifiers_validate",
                kwargs={
                    "ad_group_id": self.ad_group.id,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    ),
                },
            ),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "deleted": {"count": 0, "dimensions": 0, "summary": []},
                    "created": {"count": 1, "dimensions": 1, "summary": [{"type": "PUBLISHER", "count": 1}]},
                }
            },
        )

        entries[0]["Bid Modifier"] = 20

        csv_writer = csv.DictWriter(csv_file, csv_columns)
        csv_writer.writeheader()
        csv_writer.writerows(entries)
        csv_file.seek(0)

        response = self.client.post(
            reverse(
                "bid_modifiers_validate",
                kwargs={
                    "ad_group_id": self.ad_group.id,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    ),
                },
            ),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(result["details"]["file"], "Errors in CSV file!")

    def test_validate_new_upload_modifiers(self):
        csv_file = NamedTemporaryFile(mode="w+", suffix=".csv")
        target_column_name = bid_modifiers.helpers.output_modifier_type(
            bid_modifiers.constants.BidModifierType.PUBLISHER
        )
        csv_columns = [target_column_name, "Source Slug", "Bid Modifier"]
        entries = [{target_column_name: "example.com", "Source Slug": self.source.bidder_slug, "Bid Modifier": "1.2"}]

        csv_writer = csv.DictWriter(csv_file, csv_columns)
        csv_writer.writeheader()
        csv_writer.writerows(entries)
        csv_file.seek(0)

        response = self.client.post(
            reverse(
                "bid_modifiers_validate_new",
                kwargs={
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    )
                },
            ),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "deleted": {"count": 0, "dimensions": 0, "summary": []},
                    "created": {"count": 1, "dimensions": 1, "summary": [{"type": "PUBLISHER", "count": 1}]},
                }
            },
        )

        entries[0]["Bid Modifier"] = 20

        csv_writer = csv.DictWriter(csv_file, csv_columns)
        csv_writer.writeheader()
        csv_writer.writerows(entries)
        csv_file.seek(0)

        response = self.client.post(
            reverse(
                "bid_modifiers_validate_new",
                kwargs={
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    )
                },
            ),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(result["details"]["file"], "Errors in CSV file!")

    def test_upload_deletes_existing_modifiers(self):
        bid_modifiers.service.set_bulk(
            self.ad_group,
            [
                bid_modifiers.service.BidModifierData(
                    bid_modifiers.BidModifierType.DEVICE, constants.DeviceType.MOBILE, None, 1.1
                ),
                bid_modifiers.service.BidModifierData(
                    bid_modifiers.BidModifierType.DEVICE, constants.DeviceType.TV, None, 1.2
                ),
            ],
        )

        self.assertEqual(bid_modifiers.BidModifier.objects.filter(ad_group=self.ad_group).count(), 2)

        csv_file = NamedTemporaryFile(mode="w+", suffix=".csv")
        target_column_name = bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.DEVICE)
        csv_columns = [target_column_name, "Bid Modifier"]
        entries = [
            {target_column_name: "TV", "Bid Modifier": "1.3"},
            {target_column_name: "DESKTOP", "Bid Modifier": "1.4"},
            {target_column_name: "TABLET", "Bid Modifier": "1.5"},
        ]

        csv_writer = csv.DictWriter(csv_file, csv_columns)
        csv_writer.writeheader()
        csv_writer.writerows(entries)
        csv_file.seek(0)

        write_history_patcher = mock.patch("core.models.ad_group.instance.AdGroupInstanceMixin.write_history")
        write_history_mock = write_history_patcher.start()

        response = self.client.post(
            reverse(
                "bid_modifiers_upload",
                kwargs={
                    "ad_group_id": self.ad_group.id,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.DEVICE
                    ),
                },
            ),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)

        self.assertEqual(bid_modifiers.BidModifier.objects.filter(ad_group=self.ad_group).count(), 3)
        self.assertEqual(
            list(
                bid_modifiers.BidModifier.objects.filter(ad_group=self.ad_group)
                .order_by("pk")
                .values_list("target", flat=True)
            ),
            [str(constants.DeviceType.TV), str(constants.DeviceType.DESKTOP), str(constants.DeviceType.TABLET)],
        )

        write_history_patcher.stop()
        write_history_mock.assert_has_calls(
            [
                mock.call(
                    "Uploaded bid modifiers. Removed 2 bid modifiers. Created 3 bid modifiers.",
                    action_type=constants.HistoryActionType.BID_MODIFIER_UPDATE,
                    user=self.user,
                )
            ]
        )

    def test_invalid_upload_does_not_delete_existing_modifiers(self):
        bid_modifiers.service.set_bulk(
            self.ad_group,
            [
                bid_modifiers.service.BidModifierData(
                    bid_modifiers.BidModifierType.DEVICE, constants.DeviceType.MOBILE, None, 1.1
                ),
                bid_modifiers.service.BidModifierData(
                    bid_modifiers.BidModifierType.DEVICE, constants.DeviceType.TV, None, 1.2
                ),
            ],
        )

        self.assertEqual(bid_modifiers.BidModifier.objects.filter(ad_group=self.ad_group).count(), 2)

        csv_file = NamedTemporaryFile(mode="w+", suffix=".csv")
        target_column_name = bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.DEVICE)
        csv_columns = [target_column_name, "Bid Modifier"]
        entries = [
            {target_column_name: "invalid", "Bid Modifier": "1.3"},
            {target_column_name: "DESKTOP", "Bid Modifier": "1.4"},
            {target_column_name: "TABLET", "Bid Modifier": "1.5"},
        ]

        csv_writer = csv.DictWriter(csv_file, csv_columns)
        csv_writer.writeheader()
        csv_writer.writerows(entries)
        csv_file.seek(0)

        response = self.client.post(
            reverse(
                "bid_modifiers_upload",
                kwargs={
                    "ad_group_id": self.ad_group.id,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.DEVICE
                    ),
                },
            ),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)

        self.assertEqual(bid_modifiers.BidModifier.objects.filter(ad_group=self.ad_group).count(), 2)
        self.assertEqual(
            list(
                bid_modifiers.BidModifier.objects.filter(ad_group=self.ad_group)
                .order_by("pk")
                .values_list("target", flat=True)
            ),
            [str(constants.DeviceType.MOBILE), str(constants.DeviceType.TV)],
        )

    def test_upload_file_format_validation_error(self):
        csv_file = NamedTemporaryFile(mode="w+", suffix=".csv")
        csv_file.write("A wizard is never late, nor is he early")
        csv_file.seek(0)

        response = self.client.post(
            reverse(
                "bid_modifiers_upload",
                kwargs={
                    "ad_group_id": self.ad_group.id,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    ),
                },
            ),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(
            result, {"errorCode": "ValidationError", "details": {"file": "Bid Modifier target column is missing"}}
        )

    @mock.patch("utils.s3helpers.S3Helper.put")
    @mock.patch("core.features.bid_modifiers.helpers.create_csv_error_key")
    def test_upload_validation_error(self, mock_create_csv_error_key, mock_s3_helper_put):
        mock_create_csv_error_key.return_value = "j4NILLm4bPUkR0ukfA475kEuKLy0uGssS5eMUfrWvSZTB9GL6oO51y9ehZwbx1vT"

        csv_file = NamedTemporaryFile(mode="w+", suffix=".csv")
        target_column_name = bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.DEVICE)
        csv_columns = [target_column_name, "Bid Modifier"]
        entries = [
            {target_column_name: constants.DeviceType.get_name(constants.DeviceType.MOBILE), "Bid Modifier": "20.0"}
        ]

        csv_writer = csv.DictWriter(csv_file, csv_columns)
        csv_writer.writeheader()
        csv_writer.writerows(entries)
        csv_file.seek(0)

        response = self.client.post(
            reverse(
                "bid_modifiers_upload",
                kwargs={
                    "ad_group_id": self.ad_group.id,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.DEVICE
                    ),
                },
            ),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(
            result,
            {
                "errorCode": "ValidationError",
                "details": {"file": "Errors in CSV file!", "errorFileUrl": mock_create_csv_error_key.return_value},
            },
        )

        mock_s3_helper_put.assert_called_once()
        csv_error_content = mock_s3_helper_put.call_args_list[0][0][1]

        error_entires = [row for row in csv.DictReader(io.StringIO(csv_error_content))]

        self.assertEqual(
            error_entires,
            [
                {
                    target_column_name: constants.DeviceType.get_name(constants.DeviceType.MOBILE),
                    "Bid Modifier": "20.0",
                    "Errors": bid_modifiers.helpers._get_modifier_bounds_error_message(20.0),
                }
            ],
        )

    def test_download_example_file(self):
        response = self.client.get(
            reverse(
                "bid_modifiers_example_download",
                kwargs={
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    )
                },
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content.decode("utf8"),
            bid_modifiers.service.make_csv_example_file(bid_modifiers.constants.BidModifierType.PUBLISHER).read(),
        )

    def test_download_bulk_example_file(self):
        response = self.client.get(reverse("bid_modifiers_example_download_bulk", kwargs={}))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.content.decode("utf8"), bid_modifiers.service.make_bulk_csv_example_file().read())

    def test_bulk_upload_and_download_modifiers(self):
        entries = [
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.PUBLISHER
                ): "example.com",
                "Source Slug": self.source.bidder_slug,
                "Bid Modifier": "1.1",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.SOURCE
                ): self.outbrain.bidder_slug,
                "Bid Modifier": "1.2",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.DEVICE
                ): constants.DeviceType.get_name(constants.DeviceType.MOBILE),
                "Bid Modifier": "1.3",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.OPERATING_SYSTEM
                ): constants.OperatingSystem.get_name(constants.OperatingSystem.ANDROID),
                "Bid Modifier": "1.4",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.PLACEMENT
                ): constants.PlacementMedium.get_name(constants.PlacementMedium.SITE),
                "Bid Modifier": "1.5",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.COUNTRY
                ): self.us.key,
                "Bid Modifier": "1.6",
            },
            {
                bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.STATE): self.tx.key,
                "Bid Modifier": "1.7",
            },
            {
                bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.DMA): self.ep.key,
                "Bid Modifier": "1.8",
            },
            {
                bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.AD): str(self.ad.id),
                "Bid Modifier": "1.9",
            },
        ]

        def sub_file_generator(entries):
            for entry in entries:
                sub_file = io.StringIO()
                csv_writer = csv.DictWriter(sub_file, entry.keys())
                csv_writer.writeheader()
                csv_writer.writerows([entry])
                sub_file.seek(0)
                yield sub_file

        csv_file = bid_modifiers.helpers.create_bulk_csv_file(sub_file_generator(entries))

        response = self.client.post(
            reverse("bid_modifiers_upload_bulk", kwargs={"ad_group_id": self.ad_group.id}),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "deleted": {
                        "count": 9,
                        "dimensions": 9,
                        "summary": [
                            {"type": "PUBLISHER", "count": 1},
                            {"type": "SOURCE", "count": 1},
                            {"type": "DEVICE", "count": 1},
                            {"type": "OPERATING_SYSTEM", "count": 1},
                            {"type": "PLACEMENT", "count": 1},
                            {"type": "COUNTRY", "count": 1},
                            {"type": "STATE", "count": 1},
                            {"type": "DMA", "count": 1},
                            {"type": "AD", "count": 1},
                        ],
                    },
                    "created": {
                        "count": 9,
                        "dimensions": 9,
                        "summary": [
                            {"type": "PUBLISHER", "count": 1},
                            {"type": "SOURCE", "count": 1},
                            {"type": "DEVICE", "count": 1},
                            {"type": "OPERATING_SYSTEM", "count": 1},
                            {"type": "PLACEMENT", "count": 1},
                            {"type": "COUNTRY", "count": 1},
                            {"type": "STATE", "count": 1},
                            {"type": "DMA", "count": 1},
                            {"type": "AD", "count": 1},
                        ],
                    },
                }
            },
        )

        self.assertEqual(
            bid_modifiers.service.get(self.ad_group),
            [
                {
                    "type": bid_modifiers.constants.BidModifierType.PUBLISHER,
                    "target": "example.com",
                    "source": self.source,
                    "modifier": 1.1,
                },
                {
                    "type": bid_modifiers.constants.BidModifierType.SOURCE,
                    "target": str(self.outbrain.id),
                    "source": None,
                    "modifier": 1.2,
                },
                {
                    "type": bid_modifiers.constants.BidModifierType.DEVICE,
                    "target": str(constants.DeviceType.MOBILE),
                    "source": None,
                    "modifier": 1.3,
                },
                {
                    "type": bid_modifiers.constants.BidModifierType.OPERATING_SYSTEM,
                    "target": constants.OperatingSystem.ANDROID,
                    "source": None,
                    "modifier": 1.4,
                },
                {
                    "type": bid_modifiers.constants.BidModifierType.PLACEMENT,
                    "target": constants.PlacementMedium.SITE,
                    "source": None,
                    "modifier": 1.5,
                },
                {
                    "type": bid_modifiers.constants.BidModifierType.COUNTRY,
                    "target": self.us.key,
                    "source": None,
                    "modifier": 1.6,
                },
                {
                    "type": bid_modifiers.constants.BidModifierType.STATE,
                    "target": self.tx.key,
                    "source": None,
                    "modifier": 1.7,
                },
                {
                    "type": bid_modifiers.constants.BidModifierType.DMA,
                    "target": self.ep.key,
                    "source": None,
                    "modifier": 1.8,
                },
                {
                    "type": bid_modifiers.constants.BidModifierType.AD,
                    "target": str(self.ad.id),
                    "source": None,
                    "modifier": 1.9,
                },
            ],
        )

        response = self.client.get(reverse("bid_modifiers_download_bulk", kwargs={"ad_group_id": self.ad_group.id}))
        self.assertEqual(response.status_code, 200)

        download_file = io.StringIO(response.content.decode("utf8"))
        csv_file.seek(0)

        self.assertEqual(download_file.read(), csv_file.read())

    def test_validate_bulk_upload_modifiers(self):
        entries = [
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.PUBLISHER
                ): "example.com",
                "Source Slug": self.source.bidder_slug,
                "Bid Modifier": "1.1",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.DEVICE
                ): constants.DeviceType.get_name(constants.DeviceType.MOBILE),
                "Bid Modifier": "1.3",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.OPERATING_SYSTEM
                ): constants.OperatingSystem.get_text(constants.OperatingSystem.ANDROID),
                "Bid Modifier": "1.4",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.PLACEMENT
                ): constants.PlacementMedium.get_name(constants.PlacementMedium.SITE),
                "Bid Modifier": "1.5",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.COUNTRY
                ): self.us.key,
                "Bid Modifier": "1.6",
            },
            {
                bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.STATE): self.tx.key,
                "Bid Modifier": "1.7",
            },
            {
                bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.DMA): self.ep.key,
                "Bid Modifier": "1.8",
            },
            {
                bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.AD): str(self.ad.id),
                "Bid Modifier": "1.9",
            },
        ]

        def sub_file_generator(entries):
            for entry in entries:
                sub_file = io.StringIO()
                csv_writer = csv.DictWriter(sub_file, entry.keys())
                csv_writer.writeheader()
                csv_writer.writerows([entry])
                sub_file.seek(0)
                yield sub_file

        csv_file = bid_modifiers.helpers.create_bulk_csv_file(sub_file_generator(entries))

        response = self.client.post(
            reverse("bid_modifiers_validate_bulk", kwargs={"ad_group_id": self.ad_group.id}),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "deleted": {"count": 0, "dimensions": 0, "summary": []},
                    "created": {
                        "count": 8,
                        "dimensions": 8,
                        "summary": [
                            {"type": "PUBLISHER", "count": 1},
                            {"type": "DEVICE", "count": 1},
                            {"type": "OPERATING_SYSTEM", "count": 1},
                            {"type": "PLACEMENT", "count": 1},
                            {"type": "COUNTRY", "count": 1},
                            {"type": "STATE", "count": 1},
                            {"type": "DMA", "count": 1},
                            {"type": "AD", "count": 1},
                        ],
                    },
                }
            },
        )

        entries[0]["Bid Modifier"] = 20

        csv_file = bid_modifiers.helpers.create_bulk_csv_file(sub_file_generator(entries))

        response = self.client.post(
            reverse("bid_modifiers_validate_bulk", kwargs={"ad_group_id": self.ad_group.id}),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(result["details"]["file"], "Errors in CSV file!")

    def test_validate_bulk_new_upload_modifiers(self):
        entries = [
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.PUBLISHER
                ): "example.com",
                "Source Slug": self.source.bidder_slug,
                "Bid Modifier": "1.1",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.DEVICE
                ): constants.DeviceType.get_name(constants.DeviceType.MOBILE),
                "Bid Modifier": "1.3",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.OPERATING_SYSTEM
                ): constants.OperatingSystem.get_text(constants.OperatingSystem.ANDROID),
                "Bid Modifier": "1.4",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.PLACEMENT
                ): constants.PlacementMedium.get_name(constants.PlacementMedium.SITE),
                "Bid Modifier": "1.5",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.COUNTRY
                ): self.us.key,
                "Bid Modifier": "1.6",
            },
            {
                bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.STATE): self.tx.key,
                "Bid Modifier": "1.7",
            },
            {
                bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.DMA): self.ep.key,
                "Bid Modifier": "1.8",
            },
            {
                bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.AD): str(self.ad.id),
                "Bid Modifier": "1.9",
            },
        ]

        def sub_file_generator(entries):
            for entry in entries:
                sub_file = io.StringIO()
                csv_writer = csv.DictWriter(sub_file, entry.keys())
                csv_writer.writeheader()
                csv_writer.writerows([entry])
                sub_file.seek(0)
                yield sub_file

        csv_file = bid_modifiers.helpers.create_bulk_csv_file(sub_file_generator(entries))

        response = self.client.post(reverse("bid_modifiers_validate_bulk_new"), {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {
                    "deleted": {"count": 0, "dimensions": 0, "summary": []},
                    "created": {
                        "count": 8,
                        "dimensions": 8,
                        "summary": [
                            {"type": "PUBLISHER", "count": 1},
                            {"type": "DEVICE", "count": 1},
                            {"type": "OPERATING_SYSTEM", "count": 1},
                            {"type": "PLACEMENT", "count": 1},
                            {"type": "COUNTRY", "count": 1},
                            {"type": "STATE", "count": 1},
                            {"type": "DMA", "count": 1},
                            {"type": "AD", "count": 1},
                        ],
                    },
                }
            },
        )

        entries[0]["Bid Modifier"] = 20

        csv_file = bid_modifiers.helpers.create_bulk_csv_file(sub_file_generator(entries))

        response = self.client.post(reverse("bid_modifiers_validate_bulk_new"), {"file": csv_file}, format="multipart")
        self.assertEqual(response.status_code, 400)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(result["details"]["file"], "Errors in CSV file!")

    @mock.patch("utils.s3helpers.S3Helper.put")
    @mock.patch("core.features.bid_modifiers.helpers.create_csv_error_key")
    def test_bulk_upload_validation_error(self, mock_create_csv_error_key, mock_s3_helper_put):
        mock_create_csv_error_key.return_value = "j4NILLm4bPUkR0ukfA475kEuKLy0uGssS5eMUfrWvSZTB9GL6oO51y9ehZwbx1vT"
        entries = [
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.PUBLISHER
                ): "example.com",
                "Bid Modifier": "1.1",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.SOURCE
                ): self.outbrain.bidder_slug,
                "Source Slug": self.source.bidder_slug,
                "Bid Modifier": "1.2",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.DEVICE
                ): constants.DeviceType.get_name(constants.DeviceType.MOBILE),
                "Bid Modifier": "11.3",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.OPERATING_SYSTEM
                ): constants.OperatingSystem.get_text(constants.OperatingSystem.ANDROID),
                "Bid Modifier": "-0.1",
            },
            {
                bid_modifiers.helpers.output_modifier_type(
                    bid_modifiers.constants.BidModifierType.PLACEMENT
                ): "illegal",
                "Bid Modifier": "1.5",
            },
            {
                bid_modifiers.helpers.output_modifier_type(bid_modifiers.constants.BidModifierType.COUNTRY): "illegal",
                "Bid Modifier": "1.6",
            },
            {"illegal": str(self.ad.id), "Bid Modifier": "-0.1"},
        ]

        def sub_file_generator(entries):
            for entry in entries:
                sub_file = io.StringIO()
                csv_writer = csv.DictWriter(sub_file, entry.keys())
                csv_writer.writeheader()
                csv_writer.writerows([entry])
                sub_file.seek(0)
                yield sub_file

        csv_file = bid_modifiers.helpers.create_bulk_csv_file(sub_file_generator(entries))

        response = self.client.post(
            reverse("bid_modifiers_upload_bulk", kwargs={"ad_group_id": self.ad_group.id}),
            {"file": csv_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        result = self.assertResponseError(response, "ValidationError")
        self.assertEqual(
            result,
            {
                "errorCode": "ValidationError",
                "details": {"file": "Errors in CSV file!", "errorFileUrl": mock_create_csv_error_key.return_value},
            },
        )

        mock_s3_helper_put.assert_called_once()
        csv_error_content = mock_s3_helper_put.call_args_list[0][0][1]

        actual_contents = csv_error_content

        expected_contents = "".join(
            [
                "Source Slug column missing in CSV file\r\n",
                "Publisher,Bid Modifier\r\n",
                "example.com,1.1\r\n",
                "\r\n",
                "Source Slug should exist only in publisher bid modifier CSV file\r\n",
                "Source,Source Slug,Bid Modifier\r\n",
                "{},{},1.2\r\n".format(self.outbrain.bidder_slug, self.source.bidder_slug),
                "\r\n",
                "Device,Bid Modifier,Errors\r\n",
                "MOBILE,11.3,Bid modifier too high: 11.3 (> 11.0)\r\n",
                "\r\n",
                "Operating System,Bid Modifier,Errors\r\n",
                "Android,-0.1,Bid modifier too low: -0.1 (< 0.01)\r\n",
                "\r\n",
                "Placement,Bid Modifier,Errors\r\n",
                "illegal,1.5,Invalid Placement Medium\r\n",
                "\r\n",
                "Country,Bid Modifier,Errors\r\n",
                "illegal,1.6,Invalid Geolocation\r\n",
                "\r\n",
                "Bid Modifier target column is missing\r\n",
                "illegal,Bid Modifier\r\n",
                "{},-0.1\r\n".format(self.ad.id),
            ]
        )

        self.assertEqual(actual_contents, expected_contents)

    @mock.patch("utils.s3helpers.S3Helper.get")
    def test_error_download(self, mock_s3_helper_get):
        mock_s3_helper_get.return_value = ""
        csv_error_key = "j4NILLm4bPUkR0ukfA475kEuKLy0uGssS5eMUfrWvSZTB9GL6oO51y9ehZwbx1vT"

        response = self.client.get(
            reverse(
                "bid_modifiers_error_download", kwargs={"ad_group_id": self.ad_group.id, "csv_error_key": csv_error_key}
            )
        )

        self.assertEqual(response.status_code, 200)

        mock_s3_helper_get.assert_called_once()

        self.assertEqual(
            mock_s3_helper_get.call_args_list[0][0][0],
            bid_modifiers.create_error_file_path(self.ad_group.id, csv_error_key),
        )

    @mock.patch("utils.s3helpers.S3Helper.get")
    def test_error_download_new(self, mock_s3_helper_get):
        mock_s3_helper_get.return_value = ""
        csv_error_key = "j4NILLm4bPUkR0ukfA475kEuKLy0uGssS5eMUfrWvSZTB9GL6oO51y9ehZwbx1vT"

        response = self.client.get(reverse("bid_modifiers_error_download_new", kwargs={"csv_error_key": csv_error_key}))

        self.assertEqual(response.status_code, 200)

        mock_s3_helper_get.assert_called_once()

        self.assertEqual(
            mock_s3_helper_get.call_args_list[0][0][0], bid_modifiers.create_error_file_path(None, csv_error_key)
        )


class NoPermissionTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        super(NoPermissionTest, self).setUp()
        test_helper.remove_permissions(self.user, ["can_set_bid_modifiers"])

    def test_download_modifiers(self):
        response = self.client.get(
            reverse(
                "bid_modifiers_download",
                kwargs={
                    "ad_group_id": 1,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    ),
                },
            )
        )
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )

    def test_upload_modifiers(self):
        response = self.client.post(
            reverse(
                "bid_modifiers_upload",
                kwargs={
                    "ad_group_id": 1,
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    ),
                },
            ),
            {"file": io.StringIO()},
            format="multipart",
        )
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )

    def test_download_example_file(self):
        response = self.client.get(
            reverse(
                "bid_modifiers_example_download",
                kwargs={
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    )
                },
            )
        )
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )

    def test_bulk_download_modifiers(self):
        response = self.client.get(reverse("bid_modifiers_download_bulk", kwargs={"ad_group_id": 1}))
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )

    def test_bulk_upload_modifiers(self):
        response = self.client.post(
            reverse("bid_modifiers_upload_bulk", kwargs={"ad_group_id": 1}), {"file": io.StringIO()}, format="multipart"
        )
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )

    def test_download_bulk_example_file(self):
        response = self.client.get(
            reverse(
                "bid_modifiers_example_download",
                kwargs={
                    "breakdown_name": bid_modifiers.helpers.modifier_type_to_breakdown_name(
                        bid_modifiers.BidModifierType.PUBLISHER
                    )
                },
            )
        )
        self.assertEqual(response.status_code, 403)
        result = self.assertResponseError(response, "PermissionDenied")
        self.assertEqual(
            result, {"errorCode": "PermissionDenied", "details": "You do not have permission to perform this action."}
        )


class BidModifierTypeSummariesTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        super(BidModifierTypeSummariesTest, self).setUp()
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__users=[self.user])
        bid_modifiers.service.set_bulk(
            self.ad_group,
            [
                bid_modifiers.service.BidModifierData(
                    bid_modifiers.BidModifierType.DEVICE, constants.DeviceType.MOBILE, None, 1.1
                ),
                bid_modifiers.service.BidModifierData(
                    bid_modifiers.BidModifierType.DEVICE, constants.DeviceType.TV, None, 1.2
                ),
            ],
        )
        self.other_ad_group = magic_mixer.blend(core.models.AdGroup)
        bid_modifiers.service.set_bulk(
            self.other_ad_group,
            [
                bid_modifiers.service.BidModifierData(
                    bid_modifiers.BidModifierType.DEVICE, constants.DeviceType.TABLET, None, 1.7
                )
            ],
        )

    def test_retrieve(self):
        response = self.client.get(reverse("bid_modifiers_type_summaries", kwargs={"ad_group_id": self.ad_group.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"data": [{"type": "DEVICE", "count": 2, "min": 1.0, "max": 1.2}]})

    def test_retrieve_foreign_ad_group(self):
        response = self.client.get(
            reverse("bid_modifiers_type_summaries", kwargs={"ad_group_id": self.other_ad_group.id})
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json(), {"errorCode": "MissingDataError", "details": "Ad Group does not exist"})
