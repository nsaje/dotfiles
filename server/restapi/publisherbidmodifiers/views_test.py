from django.core.urlresolvers import reverse
from utils.magic_mixer import magic_mixer, get_request_mock
from tempfile import NamedTemporaryFile
import restapi.common.views_base_test
import core.models
import csv

from core.features.publisher_bid_modifiers import service


class PublisherBidModifierCSVTest(restapi.common.views_base_test.RESTAPITest):
    def setUp(self):
        super(PublisherBidModifierCSVTest, self).setUp()
        self.test_request = get_request_mock(self.user)
        self.test_source = magic_mixer.blend(core.models.Source, bidder_slug="test_slug")
        self.test_ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account__users=[self.user])

    def test_update_modifiers(self):
        csv_file = NamedTemporaryFile(mode="w+", suffix=".csv")
        csv_columns = ["Publisher", "Source Slug", "Bid Modifier"]
        entries = [
            {"Publisher": "example.com", "Source Slug": "test_slug", "Bid Modifier": ""},
            {"Publisher": "example2.com", "Source Slug": "test_slug", "Bid Modifier": "1.0"},
            {"Publisher": "example3.com", "Source Slug": "test_slug", "Bid Modifier": "2.0"},
            {"Publisher": "example4.com", "Source Slug": "test_slug", "Bid Modifier": "0.5"},
        ]

        csv_writer = csv.DictWriter(csv_file, csv_columns)
        csv_writer.writeheader()
        csv_writer.writerows(entries)
        csv_file.seek(0)

        response = self.client.post(
            reverse("publisher_bid_modifiers_upload", kwargs={"ad_group_id": self.test_ad_group.id}),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)

        updated_modifiers = service.get(self.test_ad_group)
        self.assertEqual(len(updated_modifiers), 2)  # Only 2, since "1.0" and "" are ignored.

        for i in range(2, 4):
            entry = entries[i]
            updated_modifier = updated_modifiers[i - 2]
            self.assertEqual(entry["Publisher"], updated_modifier["publisher"])
            self.assertEqual(entry["Source Slug"], updated_modifier["source"].get_clean_slug())
            self.assertEqual(float(entry["Bid Modifier"]), updated_modifier["modifier"])

    def test_bad_csv_is_rejected(self):
        csv_file = NamedTemporaryFile(mode="w+", suffix=".csv")
        csv_file.write("A wizard is never late, nor is he early")
        csv_file.seek(0)

        response = self.client.post(
            reverse("publisher_bid_modifiers_upload", kwargs={"ad_group_id": self.test_ad_group.id}),
            {"file": csv_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, 400)
