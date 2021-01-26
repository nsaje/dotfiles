# -*- coding: utf-8 -*-
import csv
import io

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ValidationError
from django.test import TestCase
from mock import Mock
from mock import patch

from dash import constants
from dash import forms
from dash import models
from utils.magic_mixer import magic_mixer
from zemauth.models import User

EXAMPLE_CSV_CONTENT = [
    forms.EXAMPLE_CSV_CONTENT["url"],
    forms.EXAMPLE_CSV_CONTENT["title"],
    forms.EXAMPLE_CSV_CONTENT["image_url"],
    "Tech Talk with Zemanta: How Content Ads Will Come to Dominant Publishers Advertising Efforts",
    "https://www.example.com/tracker",
]


class AdGroupAdminFormTest(TestCase):
    fixtures = ["test_models.yaml"]

    def setUp(self):
        self.request = Mock()
        user = User()
        user.save()
        self.request.user = user

    def test_instance_without_settings(self):
        ad_group = magic_mixer.blend(models.AdGroup, name="Test", campaign_id=1)
        form = forms.AdGroupAdminForm(instance=ad_group)
        self.assertEqual("", form.initial["notes"])
        self.assertEqual([], form.initial["bluekai_targeting"])

    def test_instance_with_settings(self):
        ad_group = magic_mixer.blend(models.AdGroup, name="Test", campaign_id=1)
        settings = ad_group.get_current_settings().copy_settings()
        settings.notes = "a"
        settings.bluekai_targeting = ["a"]
        settings.interest_targeting = ["a"]
        settings.exclusion_interest_targeting = ["a"]
        settings.save(None)

        form = forms.AdGroupAdminForm(instance=ad_group)
        self.assertEqual("a", form.initial["notes"])
        self.assertEqual(["a"], form.initial["bluekai_targeting"])


class AdGroupAdsUploadFormTest(TestCase):
    def setUp(self):
        self.request = magic_mixer.blend_request_user(permissions=["can_use_3rdparty_js_trackers"])

        self.batch_name = "Test batch name"
        self.url = "http://example.com"
        self.title = "Test Title"
        self.image_url = "http://example.com/image"
        self.crop_areas = "(((44, 22), (144, 122)), ((33, 22), (177, 122)))"
        self.display_url = "example.com"
        self.description = "testdescription"
        self.brand_name = "testbrandname"
        self.call_to_action = "testcalltoaction"
        self.primary_tracker_url = "http://example1.com"
        self.file_contents = [
            ["URL", "title", "image URL", "crop areas"],
            [
                "http://www.nextadvisor.com/blog/2014/12/11/best-credit-cards-2015/?kw=zem_dsk_bc15q15_33",
                "See The Best Credit Cards of 2015",
                "http://i.zemanta.com/319205478_350_350.jpg",
                self.crop_areas,
            ],
        ]

        self.tracker_1_event_type = constants.TrackerEventType.IMPRESSION
        self.tracker_1_method = constants.TrackerMethod.JS
        self.tracker_1_url = "https://t.tracker1.com/tracker.js"
        self.tracker_1_fallback_url = "https://t.tracker1.com/fallback.png"
        self.tracker_1_optional = False
        self.tracker_2_event_type = constants.TrackerEventType.IMPRESSION
        self.tracker_2_method = constants.TrackerMethod.JS
        self.tracker_2_url = "https://t.tracker2.com/tracker.js"
        self.tracker_2_fallback_url = "https://t.tracker2.com/fallback.png"
        self.tracker_2_optional = False
        self.tracker_3_event_type = constants.TrackerEventType.IMPRESSION
        self.tracker_3_method = constants.TrackerMethod.JS
        self.tracker_3_url = "https://t.tracker3.com/tracker.js"
        self.tracker_3_fallback_url = "https://t.tracker3.com/fallback.png"
        self.tracker_3_optional = False

    def test_parse_unknown_file(self):
        csv_file = self._get_csv_file(["Url", "Title", "Image Url", "Crop Areas"], [])
        form = self._init_form(csv_file, {})
        with open("./dash/test_files/test.gif", "rb") as f:
            with self.assertRaises(ValidationError):
                form._parse_file(f)
        with open("./dash/test_files/test.jpg", "rb") as f:
            with self.assertRaises(ValidationError):
                form._parse_file(f)

    def test_parse_csv_file(self):
        csv_file = self._get_csv_file(["Url", "Title", "Image Url", "Crop Areas"], [])
        form = self._init_form(csv_file, {})
        with open("./dash/test_files/test.csv", "rb") as f:
            rows = form._parse_file(f)
            self.assertEqual(self.file_contents, rows)

    def test_parse_xls_file(self):
        csv_file = self._get_csv_file(["Url", "Title", "Image Url", "Crop Areas"], [])
        form = self._init_form(csv_file, {})
        with open("./dash/test_files/test.xls", "rb") as f:
            rows = form._parse_file(f)
            self.assertEqual(self.file_contents, rows)

    def test_parse_xlsx_file(self):
        csv_file = self._get_csv_file(["Url", "Title", "Image Url", "Crop Areas"], [])
        form = self._init_form(csv_file, {})
        with open("./dash/test_files/test.xlsx", "rb") as f:
            rows = form._parse_file(f)
            self.assertEqual(self.file_contents, rows)

    def test_missing_all_columns(self):
        csv_file = self._get_csv_file([], ["http://example.com", "Example", "img.jpg"])

        form = self._init_form(csv_file, {"display_url": "test.com"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"candidates": ["First column in header should be URL."]})

    def test_missing_title_and_image_url(self):
        csv_file = self._get_csv_file(["Url"], ["http://example.com", "Example", "img.jpg"])

        form = self._init_form(csv_file, {"display_url": "test.com"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"candidates": ["Second column in header should be Title."]})

    def test_missing_image_url(self):
        csv_file = self._get_csv_file(["Url", "Title"], ["http://example.com", "Example", "img.jpg"])

        form = self._init_form(csv_file, {"display_url": "test.com"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"candidates": ["Third column in header should be Image URL."]})

    def test_no_csv_content(self):
        csv_file = self._get_csv_file(["Url", "Title", "Image Url", "Primary impression tracker url"], [])

        form = self._init_form(csv_file, {"display_url": "test.com"})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"candidates": ["Uploaded file is empty."]})

    def test_csv_empty_lines(self):
        csv_file = self._get_csv_file(
            [],
            [
                ["Url", "Title", "Image Url", "Primary impression tracker url"],
                [],
                [self.url, self.title, self.image_url, self.primary_tracker_url],
                [],
            ],
        )
        form = self._init_form(csv_file, None)
        self.assertTrue(form.is_valid())

    def test_csv_max_ads(self):
        lines = [[self.url, self.title, self.image_url, self.primary_tracker_url]] * 101
        csv_file = self._get_csv_file(["Url", "Title", "Image Url", "Primary impression tracker url"], lines)
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"candidates": ["Too many content ads (max. 100)"]})

    def test_csv_max_ads_empty_lines(self):
        lines = [["Url", "Title", "Image Url", "Primary impression tracker url"]]
        lines += [[self.url, self.title, self.image_url, self.primary_tracker_url], []] * 100
        csv_file = self._get_csv_file([], lines)
        form = self._init_form(csv_file, None)
        self.assertTrue(form.is_valid())

    def test_csv_example_content_without_data(self):
        csv_file = self._get_csv_file(
            ["Url", "Title", "Image Url", "Description", "Primary impression tracker url"], [EXAMPLE_CSV_CONTENT]
        )
        form = self._init_form(csv_file, {})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {"candidates": ["Uploaded file is empty."]})

    def test_csv_example_content_with_data(self):
        csv_file = self._get_csv_file(
            ["Url", "Title", "Image Url", "Description", "Primary impression tracker url"],
            [
                EXAMPLE_CSV_CONTENT,
                [self.url, self.title, self.image_url, self.description, self.primary_tracker_url],
                EXAMPLE_CSV_CONTENT,
            ],
        )
        form = self._init_form(csv_file, {})
        self.assertTrue(form.is_valid())
        self.assertEqual(len(form.cleaned_data["candidates"]), 1)

    def test_csv_impression_trackers_column(self):
        csv_file = self._get_csv_file(
            ["Url", "Title", "Image Url", "Primary impression tracker url"],
            [[self.url, self.title, self.image_url, self.primary_tracker_url]],
        )

        form = self._init_form(csv_file, None)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["candidates"][0]["primary_tracker_url"], self.primary_tracker_url)

    def test_csv_trackers_columns(self):
        csv_file = self._get_csv_file(
            [
                "Url",
                "Title",
                "Image Url",
                "Tracker 1 Event type",
                "Tracker 1 Method",
                "Tracker 1 URL",
                "Tracker 1 Fallback URL",
                "Tracker 1 Optional",
                "Tracker 2 Event type",
                "Tracker 2 Method",
                "Tracker 2 URL",
                "Tracker 2 Fallback URL",
                "Tracker 2 Optional",
                "Tracker 3 Event type",
                "Tracker 3 Method",
                "Tracker 3 URL",
                "Tracker 3 Fallback URL",
                "Tracker 3 Optional",
            ],
            [
                [
                    self.url,
                    self.title,
                    self.image_url,
                    self.tracker_1_event_type,
                    self.tracker_1_method,
                    self.tracker_1_url,
                    self.tracker_1_fallback_url,
                    self.tracker_1_optional,
                    self.tracker_2_event_type,
                    self.tracker_2_method,
                    self.tracker_2_url,
                    self.tracker_2_fallback_url,
                    self.tracker_2_optional,
                    self.tracker_3_event_type,
                    self.tracker_3_method,
                    self.tracker_3_url,
                    self.tracker_3_fallback_url,
                    self.tracker_3_optional,
                ]
            ],
        )

        form = self._init_form(csv_file, None)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["candidates"][0]["trackers"],
            [
                {
                    "event_type": self.tracker_1_event_type,
                    "method": self.tracker_1_method,
                    "url": self.tracker_1_url,
                    "fallback_url": self.tracker_1_fallback_url,
                    "tracker_optional": False,
                    "supported_privacy_frameworks": [],
                },
                {
                    "event_type": self.tracker_2_event_type,
                    "method": self.tracker_2_method,
                    "url": self.tracker_2_url,
                    "fallback_url": self.tracker_2_fallback_url,
                    "tracker_optional": False,
                    "supported_privacy_frameworks": [],
                },
                {
                    "event_type": self.tracker_3_event_type,
                    "method": self.tracker_3_method,
                    "url": self.tracker_3_url,
                    "fallback_url": self.tracker_3_fallback_url,
                    "tracker_optional": False,
                    "supported_privacy_frameworks": [],
                },
            ],
        )

    def test_csv_ignore_errors_column(self):
        csv_file = self._get_csv_file(
            ["Url", "Title", "Image Url", "Errors"], [[self.url, self.title, self.image_url, "some errors"]]
        )

        form = self._init_form(csv_file, None)
        self.assertTrue(form.is_valid())
        self.assertTrue("errors" not in form.cleaned_data["candidates"][0])

    def test_form(self):
        csv_file = self._get_csv_file(
            ["Url", "Title", "Image Url", "Primary impression tracker url"],
            [[self.url, self.title, self.image_url, self.primary_tracker_url]],
        )

        form = self._init_form(csv_file, None)

        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data,
            {
                "ad_group_id": None,
                "account_id": None,
                "batch_name": self.batch_name,
                "candidates": [
                    {
                        "image_url": self.image_url,
                        "title": self.title,
                        "url": self.url,
                        "primary_tracker_url": self.primary_tracker_url,
                        "trackers": [
                            {
                                "event_type": constants.TrackerEventType.IMPRESSION,
                                "method": constants.TrackerMethod.IMG,
                                "url": "http://example1.com",
                                "fallback_url": None,
                                "tracker_optional": True,
                                "supported_privacy_frameworks": [],
                            }
                        ],
                    }
                ],
            },
        )

    def test_form_optional_fields_duplicated(self):
        csv_file = self._get_csv_file(
            ["Url", "Title", "Image Url", "Primary impression tracker url", "Primary impression tracker url"],
            [[self.url, self.title, self.image_url, self.crop_areas, self.primary_tracker_url]],
        )

        form = self._init_form(csv_file, None)
        self.assertEqual(
            form.errors,
            {"candidates": ['Column "Primary impression tracker url" appears multiple times (2) in the CSV file.']},
        )

    def test_incorrect_csv_format(self):
        csv_file = io.BytesIO()
        csv_file.write(b"TEST\x00TEST")

        form = self._init_form(csv_file, {"batch_name": self.batch_name})

        self.assertFalse(form.is_valid())

    def test_batch_name_missing(self):
        csv_file = self._get_csv_file(["Url", "Title", "Image Url", "Crop Areas"], [])
        form = self._init_form(csv_file, {"batch_name": None})

        self.assertFalse(form.is_valid())

    def test_header_no_url(self):
        csv_file = self._get_csv_file(["aaa", "Title", "Image Url", "Crop Areas"], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["candidates"], ["First column in header should be URL."])

    def test_header_no_title(self):
        csv_file = self._get_csv_file(["URL", "aaa", "Image Url", "Crop Areas"], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["candidates"], ["Second column in header should be Title."])

    def test_header_no_image_url(self):
        csv_file = self._get_csv_file(["URL", "Title", "aaa", "Crop Areas"], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["candidates"], ["Third column in header should be Image URL."])

    def test_header_unknown_forth_column(self):
        csv_file = self._get_csv_file(["URL", "Title", "Image URL", "aaa"], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["candidates"], ['Unrecognized column name "aaa".'])

    def test_header_unknown_fifth_column(self):
        csv_file = self._get_csv_file(["URL", "Title", "Image URL", "Primary impression tracker url", "aaa"], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["candidates"], ['Unrecognized column name "aaa".'])

    def test_windows_1252_encoding(self):
        csv_file = self._get_csv_file(
            ["URL", "Title", "Image URL", "Primary impression tracker url"],
            [[self.url, "\u00ae", self.image_url, self.crop_areas]],
            encoding="windows-1252",
        )
        form = self._init_form(csv_file, None)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["candidates"][0]["title"], "\xae")

    def _init_form(self, csv_file, data_updates):
        data = {"batch_name": self.batch_name}

        if data_updates is not None:
            data.update(data_updates)

        return forms.AdGroupAdsUploadForm(
            data, {"candidates": SimpleUploadedFile("test_file.csv", csv_file.getvalue())}, user=self.request.user
        )

    def _get_csv_file(self, header, rows, encoding="utf-8"):
        csv_string = io.StringIO()

        writer = csv.writer(csv_string)
        writer.writerow(header)

        for row in rows:
            writer.writerow(row)

        return io.BytesIO(csv_string.getvalue().encode(encoding))


class ContentAdCandidateFormTestCase(TestCase):
    def _get_valid_data(self):
        data = {
            "label": "label",
            "url": "http://zemanta.com",
            "title": "Title",
            "state": constants.ContentAdSourceState.INACTIVE,
            "image_url": "http://zemanta.com/img.jpg",
            "image_crop": "center",
            "display_url": "zemanta.com",
            "brand_name": "Zemanta",
            "description": "Description",
            "call_to_action": "Read more",
            "primary_tracker_url": "https://zemanta.com/px1",
            "secondary_tracker_url": "https://zemanta.com/px2",
            "video_asset_id": "12345678-abcd-1234-abcd-123abcd12345",
            "trackers": [
                {
                    "url": "https://zemanta.com/px1",
                    "fallback_url": None,
                    "method": constants.TrackerMethod.IMG,
                    "event_type": constants.TrackerEventType.IMPRESSION,
                    "tracker_optional": False,
                },
                {
                    "url": "https://zemanta.com/px2",
                    "fallback_url": None,
                    "method": constants.TrackerMethod.IMG,
                    "event_type": constants.TrackerEventType.IMPRESSION,
                    "tracker_optional": False,
                },
            ],
        }
        files = {"image": self.valid_image}
        return data, files

    def setUp(self):
        magic_mixer.blend(models.VideoAsset, id="12345678-abcd-1234-abcd-123abcd12345")

        self.valid_image = SimpleUploadedFile(
            name="test.jpg", content=open("./dash/test_files/test.jpg", "rb").read(), content_type="image/jpg"
        )
        self.invalid_image = SimpleUploadedFile(
            name="test.jpg", content=open("./dash/test_files/test.csv", "rb").read(), content_type="text/csv"
        )

    def test_valid(self):
        f = forms.ContentAdCandidateForm(None, *self._get_valid_data())
        self.assertTrue(f.is_valid())
        self.assertEqual(
            f.cleaned_data,
            {
                "label": "label",
                "url": "http://zemanta.com",
                "title": "Title",
                "state": constants.ContentAdSourceState.INACTIVE,
                "type": constants.AdType.VIDEO,
                "image": self.valid_image,
                "image_url": "http://zemanta.com/img.jpg",
                "image_crop": "center",
                "image_height": None,
                "image_width": None,
                "icon": None,
                "icon_url": None,
                "icon_height": None,
                "icon_width": None,
                "video_asset_id": "12345678-abcd-1234-abcd-123abcd12345",
                "ad_tag": None,
                "display_url": "zemanta.com",
                "brand_name": "Zemanta",
                "description": "Description",
                "call_to_action": "Read more",
                "primary_tracker_url": "https://zemanta.com/px1",
                "secondary_tracker_url": "https://zemanta.com/px2",
                "trackers": [
                    {
                        "url": "https://zemanta.com/px1",
                        "fallback_url": None,
                        "method": "img",
                        "event_type": "impression",
                        "supported_privacy_frameworks": [],
                        "tracker_optional": False,
                    },
                    {
                        "url": "https://zemanta.com/px2",
                        "fallback_url": None,
                        "method": "img",
                        "event_type": "impression",
                        "supported_privacy_frameworks": [],
                        "tracker_optional": False,
                    },
                ],
                "trackers_status": None,
                "additional_data": None,
            },
        )

    def test_invalid_image(self):
        data, files = self._get_valid_data()
        files["image"] = self.invalid_image
        f = forms.ContentAdCandidateForm(None, data, files)
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors["image"], ["Invalid image file"])

    def test_capitalized_image_crop(self):
        data, files = self._get_valid_data()
        data["image_crop"] = "Center"
        f = forms.ContentAdCandidateForm(None, data, files)
        self.assertTrue(f.is_valid())

    def test_skipped_image_crop(self):
        data, files = self._get_valid_data()
        del data["image_crop"]
        f = forms.ContentAdCandidateForm(None, data, files)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["image_crop"], "center")

    def test_empty_image_crop(self):
        data, files = self._get_valid_data()
        data["image_crop"] = ""
        f = forms.ContentAdCandidateForm(None, data, files)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["image_crop"], "center")

    def test_valid_icon(self):
        data, files = self._get_valid_data()
        files["icon"] = self.valid_image
        data["icon_url"] = "http://zemanta.com/img.jpg"
        f = forms.ContentAdCandidateForm(None, data, files)
        self.assertTrue(f.is_valid())
        self.assertEqual(
            f.cleaned_data,
            {
                "label": "label",
                "url": "http://zemanta.com",
                "title": "Title",
                "state": constants.ContentAdSourceState.INACTIVE,
                "type": constants.AdType.VIDEO,
                "image": self.valid_image,
                "image_url": "http://zemanta.com/img.jpg",
                "image_crop": "center",
                "image_height": None,
                "image_width": None,
                "icon": self.valid_image,
                "icon_url": "http://zemanta.com/img.jpg",
                "icon_height": None,
                "icon_width": None,
                "video_asset_id": "12345678-abcd-1234-abcd-123abcd12345",
                "ad_tag": None,
                "display_url": "zemanta.com",
                "brand_name": "Zemanta",
                "description": "Description",
                "call_to_action": "Read more",
                "primary_tracker_url": "https://zemanta.com/px1",
                "secondary_tracker_url": "https://zemanta.com/px2",
                "trackers": [
                    {
                        "url": "https://zemanta.com/px1",
                        "fallback_url": None,
                        "method": "img",
                        "event_type": "impression",
                        "supported_privacy_frameworks": [],
                        "tracker_optional": False,
                    },
                    {
                        "url": "https://zemanta.com/px2",
                        "fallback_url": None,
                        "method": "img",
                        "event_type": "impression",
                        "supported_privacy_frameworks": [],
                        "tracker_optional": False,
                    },
                ],
                "trackers_status": None,
                "additional_data": None,
            },
        )

    def test_invalid_icon(self):
        data, files = self._get_valid_data()
        files["icon"] = self.invalid_image
        f = forms.ContentAdCandidateForm(None, data, files)
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors["icon"], ["Invalid image file"])

    def test_skipped_call_to_action(self):
        data, files = self._get_valid_data()
        del data["call_to_action"]
        f = forms.ContentAdCandidateForm(None, data, files)
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["call_to_action"], "Read more")

    def test_ad_tag(self):
        data, files = self._get_valid_data()
        data["type"] = constants.AdType.AD_TAG
        data["ad_tag"] = "<body></body>"
        data["image_width"] = 300
        data["image_height"] = 250
        del data["image_url"]
        del data["image_crop"]
        del data["video_asset_id"]
        del data["display_url"]
        del data["brand_name"]
        del data["description"]
        del data["call_to_action"]
        del data["primary_tracker_url"]
        del data["secondary_tracker_url"]
        f = forms.ContentAdCandidateForm(None, data, files)
        self.assertTrue(f.is_valid())
        self.assertEqual("<body></body>", f.cleaned_data["ad_tag"])
        self.assertEqual("center", f.cleaned_data["image_crop"])
        self.assertEqual("", f.cleaned_data["display_url"])
        self.assertEqual("", f.cleaned_data["brand_name"])
        self.assertEqual("", f.cleaned_data["description"])
        self.assertEqual(constants.DEFAULT_CALL_TO_ACTION, f.cleaned_data["call_to_action"])

    def test_too_many_trackers(self):
        data, files = self._get_valid_data()
        data["trackers"] = [
            {
                "url": "https://zemanta.com/px1",
                "fallback_url": None,
                "method": constants.TrackerMethod.IMG,
                "event_type": constants.TrackerEventType.IMPRESSION,
                "tracker_optional": False,
            },
            {
                "url": "https://zemanta.com/px2",
                "fallback_url": None,
                "method": constants.TrackerMethod.IMG,
                "event_type": constants.TrackerEventType.IMPRESSION,
                "tracker_optional": False,
            },
            {
                "url": "https://zemanta.com/px3",
                "fallback_url": None,
                "method": constants.TrackerMethod.IMG,
                "event_type": constants.TrackerEventType.IMPRESSION,
                "tracker_optional": False,
            },
            {
                "url": "https://zemanta.com/px4",
                "fallback_url": None,
                "method": constants.TrackerMethod.IMG,
                "event_type": constants.TrackerEventType.IMPRESSION,
                "tracker_optional": False,
            },
        ]
        f = forms.ContentAdForm(None, data, files)
        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors["trackers"], ["A maximum of three trackers is supported."])

    def test_invalid_url_trackers(self):
        data, files = self._get_valid_data()
        data["trackers"] = [
            {
                "url": "https://zemanta.com/px1",
                "fallback_url": None,
                "method": constants.TrackerMethod.IMG,
                "event_type": constants.TrackerEventType.IMPRESSION,
                "tracker_optional": False,
            },
            {
                "url": "http://zemanta.com/px2",
                "fallback_url": "http://zemanta.com/px2",
                "method": constants.TrackerMethod.IMG,
                "event_type": constants.TrackerEventType.IMPRESSION,
                "tracker_optional": False,
            },
            {
                "url": "https://zemanta.com/šš",
                "fallback_url": "https://zemanta.com/šš",
                "method": constants.TrackerMethod.IMG,
                "event_type": constants.TrackerEventType.IMPRESSION,
                "tracker_optional": False,
            },
        ]
        f = forms.ContentAdForm(None, data, files)
        self.assertFalse(f.is_valid())
        self.assertEqual(
            f.errors["trackers"],
            [
                '[{}, {"url": "Impression tracker URLs have to be HTTPS", "fallback_url": "Impression tracker URLs have to be HTTPS"}, {"url": "Invalid impression tracker URL", "fallback_url": "Invalid impression tracker URL"}]'
            ],
        )


@patch("django.conf.settings.HARDCODED_ACCOUNT_ID_OEN", 305)
class ContentAdFormTestCase(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(models.Campaign, type=constants.CampaignType.CONTENT)

    def _get_valid_data(self):
        return {
            "label": "label",
            "url": "http://zemanta.com",
            "title": "Title",
            "image_url": "http://zemanta.com/img.jpg",
            "image_crop": "center",
            "display_url": "zemanta.com",
            "brand_name": "Zemanta",
            "description": "Description",
            "call_to_action": "Read more",
            "primary_tracker_url": "https://zemanta.com/px1",
            "secondary_tracker_url": "https://zemanta.com/px2",
            "image_id": "id123",
            "image_hash": "imagehash",
            "image_width": 500,
            "image_height": 500,
            "image_file_size": 120000,
            "image_status": constants.AsyncUploadJobStatus.OK,
            "icon_url": None,
            "icon_id": None,
            "icon_hash": None,
            "icon_width": None,
            "icon_height": None,
            "icon_file_size": None,
            "icon_status": constants.AsyncUploadJobStatus.PENDING_START,
            "url_status": constants.AsyncUploadJobStatus.OK,
        }

    def _get_valid_icon_data(self):
        data = self._get_valid_data()
        data["icon_url"] = "http://zemanta.com/img.jpg"
        data["icon_id"] = "id234"
        data["icon_hash"] = "iconhash"
        data["icon_width"] = 200
        data["icon_height"] = 200
        data["icon_file_size"] = 120000
        data["icon_status"] = constants.AsyncUploadJobStatus.OK
        return data

    def test_form(self):
        f = forms.ContentAdForm(self.campaign, self._get_valid_data())
        self.assertTrue(f.is_valid())
        self.assertIsNone(f.cleaned_data["icon_url"])
        self.assertIsNone(f.cleaned_data["icon_id"])
        self.assertIsNone(f.cleaned_data["icon_hash"])
        self.assertIsNone(f.cleaned_data["icon_width"])
        self.assertIsNone(f.cleaned_data["icon_height"])
        self.assertIsNone(f.cleaned_data["icon_file_size"])
        self.assertIsNone(f.cleaned_data["original_content_ad_id"])

    def test_original_content_ad(self):
        data = self._get_valid_data()
        data["state"] = constants.ContentAdSourceState.INACTIVE
        original_content_ad = magic_mixer.blend(models.ContentAd, state=constants.ContentAdSourceState.ACTIVE)
        f = forms.ContentAdForm(self.campaign, data, original_content_ad=original_content_ad)
        self.assertTrue(f.is_valid())
        self.assertEqual(original_content_ad.id, f.cleaned_data["original_content_ad_id"])
        self.assertEqual(constants.ContentAdSourceState.ACTIVE, f.cleaned_data["state"])

    def test_image_status_pending_start(self):
        data = self._get_valid_data()
        data["image_status"] = constants.AsyncUploadJobStatus.PENDING_START
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"__all__": ["Content ad still processing"]}, f.errors)

    def test_image_status_waiting_response(self):
        data = self._get_valid_data()
        data["image_status"] = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"__all__": ["Content ad still processing"]}, f.errors)

    def test_url_status_pending_start(self):
        data = self._get_valid_data()
        data["url_status"] = constants.AsyncUploadJobStatus.PENDING_START
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"__all__": ["Content ad still processing"]}, f.errors)

    def test_url_status_waiting_response(self):
        data = self._get_valid_data()
        data["url_status"] = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"__all__": ["Content ad still processing"]}, f.errors)

    def test_invalid_image_status(self):
        data = self._get_valid_data()
        data["image_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_no_image_url_and_invalid_status(self):
        data = self._get_valid_data()
        data["image_url"] = None
        data["image_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Missing image"]}, f.errors)

    def test_not_reachable_url(self):
        data = self._get_valid_data()
        data["url_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Content unreachable or invalid"]}, f.errors)

    def test_no_url_and_invalid_status(self):
        data = self._get_valid_data()
        data["url"] = None
        data["url_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Missing URL"]}, f.errors)

    def test_missing_image_id(self):
        data = self._get_valid_data()
        del data["image_id"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_missing_image_hash(self):
        data = self._get_valid_data()
        del data["image_hash"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_missing_image_width(self):
        data = self._get_valid_data()
        del data["image_width"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_missing_image_height(self):
        data = self._get_valid_data()
        del data["image_height"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_image_min_width(self):
        data = self._get_valid_data()
        data["image_width"] = 1
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image too small (minimum size is 300x300 px)"]}, f.errors)

    def test_image_max_width(self):
        data = self._get_valid_data()
        data["image_width"] = 40001
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image too big (maximum size is 10000x10000 px)"]}, f.errors)

    def test_image_width_oen(self):
        self.campaign.account.id = settings.HARDCODED_ACCOUNT_ID_OEN
        data = self._get_valid_data()
        data["image_width"] = 1
        f = forms.ContentAdForm(self.campaign, data)
        self.assertTrue(f.is_valid())

    def test_image_min_height(self):
        data = self._get_valid_data()
        data["image_height"] = 1
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image too small (minimum size is 300x300 px)"]}, f.errors)

    def test_image_max_height(self):
        data = self._get_valid_data()
        data["image_height"] = 40001
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image too big (maximum size is 10000x10000 px)"]}, f.errors)

    def test_image_height_oen(self):
        self.campaign.account.id = settings.HARDCODED_ACCOUNT_ID_OEN
        data = self._get_valid_data()
        data["image_height"] = 1
        f = forms.ContentAdForm(self.campaign, data)
        self.assertTrue(f.is_valid())

    def test_icon(self):
        data = self._get_valid_icon_data()
        f = forms.ContentAdForm(self.campaign, data)
        self.assertTrue(f.is_valid())
        self.assertEqual("http://zemanta.com/img.jpg", f.cleaned_data["icon_url"])
        self.assertEqual("id234", f.cleaned_data["icon_id"])
        self.assertEqual("iconhash", f.cleaned_data["icon_hash"])
        self.assertEqual(200, f.cleaned_data["icon_width"])
        self.assertEqual(200, f.cleaned_data["icon_height"])
        self.assertEqual(120000, f.cleaned_data["icon_file_size"])
        self.assertEqual(constants.AsyncUploadJobStatus.OK, f.cleaned_data["icon_status"])

    def test_no_icon_and_invalid_status(self):
        data = self._get_valid_data()
        data["icon_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(self.campaign, data)
        self.assertTrue(f.is_valid())

    def test_icon_status_pending_start(self):
        data = self._get_valid_icon_data()
        data["icon_status"] = constants.AsyncUploadJobStatus.PENDING_START
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"__all__": ["Content ad still processing"]}, f.errors)

    def test_icon_status_waiting_response(self):
        data = self._get_valid_icon_data()
        data["icon_status"] = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"__all__": ["Content ad still processing"]}, f.errors)

    def test_invalid_icon_url(self):
        data = self._get_valid_icon_data()
        data["icon_url"] = "ttp://example.com"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"icon_url": ["Invalid image URL"]}, f.errors)

    def test_invalid_icon_status(self):
        data = self._get_valid_icon_data()
        data["icon_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"icon_url": ["Image could not be processed"]}, f.errors)

    def test_missing_icon_id(self):
        data = self._get_valid_icon_data()
        del data["icon_id"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"icon_url": ["Image could not be processed"]}, f.errors)

    def test_missing_icon_hash(self):
        data = self._get_valid_icon_data()
        del data["icon_hash"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"icon_url": ["Image could not be processed"]}, f.errors)

    def test_missing_icon_width(self):
        data = self._get_valid_icon_data()
        del data["icon_width"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"icon_url": ["Image could not be processed"]}, f.errors)

    def test_missing_icon_height(self):
        data = self._get_valid_icon_data()
        del data["icon_height"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"icon_url": ["Image could not be processed"]}, f.errors)

    def test_is_icon_square(self):
        data = self._get_valid_icon_data()
        data["icon_width"] = data["icon_height"] + 1
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"icon_url": ["Image height and width must be equal"]}, f.errors)

    def test_icon_min_size(self):
        data = self._get_valid_icon_data()
        data["icon_height"] = 1
        data["icon_width"] = 1
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"icon_url": ["Image too small (minimum size is 128x128 px)"]}, f.errors)

    def test_icon_max_size(self):
        data = self._get_valid_icon_data()
        data["icon_height"] = 40001
        data["icon_width"] = 40001
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"icon_url": ["Image too big (maximum size is 10000x10000 px)"]}, f.errors)

    def test_icon_size_oen(self):
        self.campaign.account.id = settings.HARDCODED_ACCOUNT_ID_OEN
        data = self._get_valid_icon_data()
        data["icon_height"] = 1
        data["icon_width"] = 1
        f = forms.ContentAdForm(self.campaign, data)
        self.assertTrue(f.is_valid())

    def test_invalid_url_status(self):
        data = self._get_valid_data()
        data["url_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Content unreachable or invalid"]}, f.errors)

    def test_label_too_long(self):
        data = self._get_valid_data()
        data["label"] = "a" * 1000
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"label": ["Label too long (max 256 characters)"]}, f.errors)

    def test_missing_url(self):
        data = self._get_valid_data()
        del data["url"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Missing URL"]}, f.errors)

    def test_url_too_long(self):
        data = self._get_valid_data()
        data["url"] = "http://example.com/" + ("repeat" * 200)
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["URL too long (max 936 characters)"]}, f.errors)

    def test_invalid_url(self):
        data = self._get_valid_data()
        data["url"] = "ttp://example.com"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Invalid URL"]}, f.errors)

    def test_missing_title(self):
        data = self._get_valid_data()
        del data["title"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"title": ["Missing title"]}, f.errors)

    def test_title_too_long(self):
        data = self._get_valid_data()
        data["title"] = "repeat" * 19
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"title": ["Title too long (max 90 characters)"]}, f.errors)

    def test_missing_image_url(self):
        data = self._get_valid_data()
        del data["image_url"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Missing image"]}, f.errors)

    def test_invalid_image_url(self):
        data = self._get_valid_data()
        data["image_url"] = "ttp://example.com"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Invalid image URL"]}, f.errors)

    def test_invalid_image_crop(self):
        data = self._get_valid_data()
        data["image_crop"] = "landscape"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_crop": ["Choose a valid image crop"]}, f.errors)

    def test_capitalized_image_crop(self):
        data = self._get_valid_data()
        data["image_crop"] = "Center"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())

    def test_empty_image_crop(self):
        data = self._get_valid_data()
        data["image_crop"] = ""
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())

    def test_missing_display_url(self):
        data = self._get_valid_data()
        del data["display_url"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"display_url": ["Missing display URL"]}, f.errors)

    def test_display_url_too_long(self):
        data = self._get_valid_data()
        data["display_url"] = "repeat" * 8 + ".com"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"display_url": ["Display URL too long (max 35 characters)"]}, f.errors)

    def test_display_url_invalid(self):
        data = self._get_valid_data()
        data["display_url"] = "test"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"display_url": ["Enter a valid URL."]}, f.errors)

    def test_display_url_with_http(self):
        data = self._get_valid_data()
        data["display_url"] = "http://" + "repeat" * 3 + ".com/"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertTrue(f.is_valid())

    def test_missing_brand_name(self):
        data = self._get_valid_data()
        del data["brand_name"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"brand_name": ["Missing brand name"]}, f.errors)

    def test_brand_name_too_long(self):
        data = self._get_valid_data()
        data["brand_name"] = "repeat" * 6
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"brand_name": ["Brand name too long (max 25 characters)"]}, f.errors)

    def test_missing_description(self):
        data = self._get_valid_data()
        del data["description"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"description": ["Missing description"]}, f.errors)

    def test_description_too_long(self):
        data = self._get_valid_data()
        data["description"] = "repeat" * 29
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"description": ["Description too long (max 150 characters)"]}, f.errors)

    def test_missing_call_to_action(self):
        data = self._get_valid_data()
        del data["call_to_action"]
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"call_to_action": ["Missing call to action"]}, f.errors)

    def test_call_to_action_too_long(self):
        data = self._get_valid_data()
        data["call_to_action"] = "repeat" * 6
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"call_to_action": ["Call to action too long (max 25 characters)"]}, f.errors)

    def test_http_primary_tracker(self):
        data = self._get_valid_data()
        data["primary_tracker_url"] = "http://zemanta.com/"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"primary_tracker_url": ["Impression tracker URLs have to be HTTPS"]}, f.errors)

    def test_http_secondary_tracker(self):
        data = self._get_valid_data()
        data["secondary_tracker_url"] = "http://zemanta.com/"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"secondary_tracker_url": ["Impression tracker URLs have to be HTTPS"]}, f.errors)

    def test_unicode_primary_tracker(self):
        data = self._get_valid_data()
        data["primary_tracker_url"] = "https://zemanta.com/š"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"primary_tracker_url": ["Invalid impression tracker URL"]}, f.errors)

    def test_unicode_secondary_tracker(self):
        data = self._get_valid_data()
        data["secondary_tracker_url"] = "https://zemanta.com/š"
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"secondary_tracker_url": ["Invalid impression tracker URL"]}, f.errors)

    def test_invalid_primary_tracker(self):
        data = self._get_valid_data()
        data["primary_tracker_url"] = "https://zemanta.com/"
        data["primary_tracker_url_status"] = 4
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"primary_tracker_url": ["Invalid or unreachable tracker URL"]}, f.errors)

    def test_invalid_secondary_tracker(self):
        data = self._get_valid_data()
        data["secondary_tracker_url"] = "https://zemanta.com/"
        data["secondary_tracker_url_status"] = 4
        f = forms.ContentAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"secondary_tracker_url": ["Invalid or unreachable tracker URL"]}, f.errors)


class ImageAdFormTestCase(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(models.Campaign, type=constants.CampaignType.DISPLAY)

    def _get_valid_data(self):
        return {
            "label": "label",
            "url": "http://zemanta.com",
            "title": "Title",
            "type": constants.AdType.IMAGE,
            "image_url": "http://zemanta.com/img.jpg",
            "display_url": "http://zemanta.com",
            "primary_tracker_url": "https://zemanta.com/px1",
            "secondary_tracker_url": "https://zemanta.com/px2",
            "image_id": "id123",
            "image_hash": "imagehash",
            "image_width": 300,
            "image_height": 250,
            "image_status": constants.AsyncUploadJobStatus.OK,
            "image_file_size": 120000,
            "url_status": constants.AsyncUploadJobStatus.OK,
        }

    def test_form(self):
        f = forms.ImageAdForm(self.campaign, self._get_valid_data())
        self.assertTrue(f.is_valid())
        self.assertIsNone(f.cleaned_data["original_content_ad_id"])

    def test_original_content_ad(self):
        data = self._get_valid_data()
        data["state"] = constants.ContentAdSourceState.INACTIVE
        original_content_ad = magic_mixer.blend(models.ContentAd, state=constants.ContentAdSourceState.ACTIVE)
        f = forms.ImageAdForm(self.campaign, data, original_content_ad=original_content_ad)
        self.assertTrue(f.is_valid())
        self.assertEqual(original_content_ad.id, f.cleaned_data["original_content_ad_id"])
        self.assertEqual(constants.ContentAdSourceState.ACTIVE, f.cleaned_data["state"])

    def test_image_status_pending_start(self):
        data = self._get_valid_data()
        data["image_status"] = constants.AsyncUploadJobStatus.PENDING_START
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"__all__": ["Content ad still processing"]}, f.errors)

    def test_image_status_waiting_response(self):
        data = self._get_valid_data()
        data["image_status"] = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"__all__": ["Content ad still processing"]}, f.errors)

    def test_url_status_pending_start(self):
        data = self._get_valid_data()
        data["url_status"] = constants.AsyncUploadJobStatus.PENDING_START
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"__all__": ["Content ad still processing"]}, f.errors)

    def test_url_status_waiting_response(self):
        data = self._get_valid_data()
        data["url_status"] = constants.AsyncUploadJobStatus.WAITING_RESPONSE
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"__all__": ["Content ad still processing"]}, f.errors)

    def test_invalid_image_status(self):
        data = self._get_valid_data()
        data["image_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_no_image_url_and_invalid_status(self):
        data = self._get_valid_data()
        data["image_url"] = None
        data["image_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Missing image"]}, f.errors)

    def test_not_reachable_url(self):
        data = self._get_valid_data()
        data["url_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Content unreachable or invalid"]}, f.errors)

    def test_no_url_and_invalid_status(self):
        data = self._get_valid_data()
        data["url"] = None
        data["url_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Missing URL"]}, f.errors)

    def test_missing_image_id(self):
        data = self._get_valid_data()
        del data["image_id"]
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_missing_image_hash(self):
        data = self._get_valid_data()
        del data["image_hash"]
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_missing_image_width(self):
        data = self._get_valid_data()
        del data["image_width"]
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_missing_image_height(self):
        data = self._get_valid_data()
        del data["image_height"]
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_missing_image_file_size(self):
        data = self._get_valid_data()
        del data["image_file_size"]
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image could not be processed"]}, f.errors)

    def test_missing_image_file_size_too_high(self):
        data = self._get_valid_data()
        data["image_file_size"] = 200000
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Image file size too big (maximum size is 150kb)"]}, f.errors)

    def test_image_supported_width(self):
        data = self._get_valid_data()
        data["image_width"] = 1
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual(
            {
                "image_url": [
                    "Image size invalid. "
                    "Supported sizes are (width "
                    "x height): 300x250, "
                    "320x50, 728x90, 336x280, "
                    "300x600, 120x600, 320x100, "
                    "468x60, 300x1050, 970x90, "
                    "970x250, 250x250, 200x200, "
                    "180x150, 125x125"
                ]
            },
            f.errors,
        )

    def test_image_supported_height(self):
        data = self._get_valid_data()
        data["image_height"] = 1
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual(
            {
                "image_url": [
                    "Image size invalid. "
                    "Supported sizes are (width "
                    "x height): 300x250, "
                    "320x50, 728x90, 336x280, "
                    "300x600, 120x600, 320x100, "
                    "468x60, 300x1050, 970x90, "
                    "970x250, 250x250, 200x200, "
                    "180x150, 125x125"
                ]
            },
            f.errors,
        )

    def test_invalid_url_status(self):
        data = self._get_valid_data()
        data["url_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Content unreachable or invalid"]}, f.errors)

    def test_label_too_long(self):
        data = self._get_valid_data()
        data["label"] = "a" * 1000
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"label": ["Label too long (max 256 characters)"]}, f.errors)

    def test_missing_url(self):
        data = self._get_valid_data()
        del data["url"]
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Missing URL"]}, f.errors)

    def test_url_too_long(self):
        data = self._get_valid_data()
        data["url"] = "http://example.com/" + ("repeat" * 200)
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["URL too long (max 936 characters)"]}, f.errors)

    def test_invalid_url(self):
        data = self._get_valid_data()
        data["url"] = "ttp://example.com"
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Invalid URL"]}, f.errors)

    def test_missing_display_url(self):
        data = self._get_valid_data()
        del data["display_url"]
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"display_url": ["Missing display URL"]}, f.errors)

    def test_display_url_too_long(self):
        data = self._get_valid_data()
        data["display_url"] = "repeat" * 8 + ".com"
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"display_url": ["Display URL too long (max 35 characters)"]}, f.errors)

    def test_display_url_invalid(self):
        data = self._get_valid_data()
        data["display_url"] = "test"
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"display_url": ["Enter a valid URL."]}, f.errors)

    def test_display_url_with_http(self):
        data = self._get_valid_data()
        data["display_url"] = "http://" + "repeat" * 3 + ".com/"
        f = forms.ImageAdForm(self.campaign, data)
        self.assertTrue(f.is_valid())

    def test_missing_title(self):
        data = self._get_valid_data()
        del data["title"]
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"title": ["Missing ad name"]}, f.errors)

    def test_title_too_long(self):
        data = self._get_valid_data()
        data["title"] = "repeat" * 19
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"title": ["Ad name too long (max 90 characters)"]}, f.errors)

    def test_missing_image_url(self):
        data = self._get_valid_data()
        del data["image_url"]
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Missing image"]}, f.errors)

    def test_invalid_image_url(self):
        data = self._get_valid_data()
        data["image_url"] = "ttp://example.com"
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_url": ["Invalid image URL"]}, f.errors)

    def test_no_unneeded_fields(self):
        data = self._get_valid_data()
        f = forms.ImageAdForm(self.campaign, data)
        self.assertTrue(f.is_valid())
        self.assertEqual("center", f.cleaned_data["image_crop"])
        self.assertEqual("", f.cleaned_data["brand_name"])
        self.assertEqual("", f.cleaned_data["description"])
        self.assertEqual(constants.DEFAULT_CALL_TO_ACTION, f.cleaned_data["call_to_action"])
        self.assertEqual(None, f.cleaned_data["additional_data"])

    def test_empty_unneeded_fields(self):
        data = self._get_valid_data()
        data["image_crop"] = ""
        data["brand_name"] = ""
        data["description"] = ""
        data["call_to_action"] = ""
        data["additional_data"] = ""
        f = forms.ImageAdForm(self.campaign, data)
        self.assertTrue(f.is_valid())
        self.assertEqual("center", f.cleaned_data["image_crop"])
        self.assertEqual("", f.cleaned_data["brand_name"])
        self.assertEqual("", f.cleaned_data["description"])
        self.assertEqual(constants.DEFAULT_CALL_TO_ACTION, f.cleaned_data["call_to_action"])
        self.assertEqual(None, f.cleaned_data["additional_data"])

    def test_http_primary_tracker(self):
        data = self._get_valid_data()
        data["primary_tracker_url"] = "http://zemanta.com/"
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"primary_tracker_url": ["Impression tracker URLs have to be HTTPS"]}, f.errors)

    def test_http_secondary_tracker(self):
        data = self._get_valid_data()
        data["secondary_tracker_url"] = "http://zemanta.com/"
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"secondary_tracker_url": ["Impression tracker URLs have to be HTTPS"]}, f.errors)

    def test_unicode_primary_tracker(self):
        data = self._get_valid_data()
        data["primary_tracker_url"] = "https://zemanta.com/š"
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"primary_tracker_url": ["Invalid impression tracker URL"]}, f.errors)

    def test_unicode_secondary_tracker(self):
        data = self._get_valid_data()
        data["secondary_tracker_url"] = "https://zemanta.com/š"
        f = forms.ImageAdForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"secondary_tracker_url": ["Invalid impression tracker URL"]}, f.errors)

    def test_no_icon_on_image_ad(self):
        data = self._get_valid_data()
        data["icon_url"] = "http://icon.com"
        data["icon_id"] = "1234id"
        data["icon_hash"] = "1234hash"
        data["icon_file_size"] = 100000
        data["icon_status"] = constants.AsyncUploadJobStatus.OK
        f = forms.ImageAdForm(self.campaign, data)
        self.assertTrue(f.is_valid())
        self.assertEqual(None, f.cleaned_data["icon_url"])
        self.assertEqual(None, f.cleaned_data["icon_id"])
        self.assertEqual(None, f.cleaned_data["icon_hash"])
        self.assertEqual(None, f.cleaned_data["icon_file_size"])
        self.assertEqual(constants.AsyncUploadJobStatus.OK, f.cleaned_data["icon_status"])


class AdTagFormTestCase(TestCase):
    def setUp(self):
        self.campaign = magic_mixer.blend(models.Campaign, type=constants.CampaignType.DISPLAY)

    def _get_valid_data(self):
        return {
            "label": "label",
            "title": "Ad tag ad",
            "url": "http://zemanta.com",
            "display_url": "http://zemanta.com",
            "type": constants.AdType.AD_TAG,
            "ad_tag": "<body></body>",
            "primary_tracker_url": "https://zemanta.com/px1",
            "secondary_tracker_url": "https://zemanta.com/px2",
            "image_width": 300,
            "image_height": 250,
            "url_status": constants.AsyncUploadJobStatus.OK,
        }

    def test_form(self):
        f = forms.AdTagForm(self.campaign, self._get_valid_data())
        self.assertTrue(f.is_valid())
        self.assertEqual(f.cleaned_data["image_status"], constants.AsyncUploadJobStatus.OK)
        self.assertIsNone(f.cleaned_data["original_content_ad_id"])

    def test_original_content_ad(self):
        data = self._get_valid_data()
        data["state"] = constants.ContentAdSourceState.INACTIVE
        original_content_ad = magic_mixer.blend(models.ContentAd, state=constants.ContentAdSourceState.ACTIVE)
        f = forms.AdTagForm(self.campaign, data, original_content_ad=original_content_ad)
        self.assertTrue(f.is_valid())
        self.assertEqual(original_content_ad.id, f.cleaned_data["original_content_ad_id"])
        self.assertEqual(constants.ContentAdSourceState.ACTIVE, f.cleaned_data["state"])

    def test_missing_ad_tag(self):
        data = self._get_valid_data()
        del data["ad_tag"]
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"ad_tag": ["Missing ad tag"]}, f.errors)

    def test_not_reachable_url(self):
        data = self._get_valid_data()
        data["url_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Content unreachable or invalid"]}, f.errors)

    def test_no_url_and_invalid_status(self):
        data = self._get_valid_data()
        data["url"] = None
        data["url_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Missing URL"]}, f.errors)

    def test_missing_image_width(self):
        data = self._get_valid_data()
        del data["image_width"]
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_width": ["Missing ad width"]}, f.errors)

    def test_missing_image_height(self):
        data = self._get_valid_data()
        del data["image_height"]
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"image_height": ["Missing ad height"]}, f.errors)

    def test_image_supported_width(self):
        data = self._get_valid_data()
        data["image_width"] = 1
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual(
            {
                "image_url": [
                    "Image size invalid. "
                    "Supported sizes are (width "
                    "x height): 300x250, "
                    "320x50, 728x90, 336x280, "
                    "300x600, 120x600, 320x100, "
                    "468x60, 300x1050, 970x90, "
                    "970x250, 250x250, 200x200, "
                    "180x150, 125x125"
                ]
            },
            f.errors,
        )

    def test_image_supported_height(self):
        data = self._get_valid_data()
        data["image_height"] = 1
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual(
            {
                "image_url": [
                    "Image size invalid. "
                    "Supported sizes are (width "
                    "x height): 300x250, "
                    "320x50, 728x90, 336x280, "
                    "300x600, 120x600, 320x100, "
                    "468x60, 300x1050, 970x90, "
                    "970x250, 250x250, 200x200, "
                    "180x150, 125x125"
                ]
            },
            f.errors,
        )

    def test_invalid_url_status(self):
        data = self._get_valid_data()
        data["url_status"] = constants.AsyncUploadJobStatus.FAILED
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Content unreachable or invalid"]}, f.errors)

    def test_label_too_long(self):
        data = self._get_valid_data()
        data["label"] = "a" * 1000
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"label": ["Label too long (max 256 characters)"]}, f.errors)

    def test_missing_display_url(self):
        data = self._get_valid_data()
        del data["display_url"]
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"display_url": ["Missing display URL"]}, f.errors)

    def test_display_url_too_long(self):
        data = self._get_valid_data()
        data["display_url"] = "repeat" * 8 + ".com"
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"display_url": ["Display URL too long (max 35 characters)"]}, f.errors)

    def test_display_url_invalid(self):
        data = self._get_valid_data()
        data["display_url"] = "test"
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"display_url": ["Enter a valid URL."]}, f.errors)

    def test_display_url_with_http(self):
        data = self._get_valid_data()
        data["display_url"] = "http://" + "repeat" * 3 + ".com/"
        f = forms.AdTagForm(self.campaign, data)
        self.assertTrue(f.is_valid())

    def test_missing_url(self):
        data = self._get_valid_data()
        del data["url"]
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Missing URL"]}, f.errors)

    def test_url_too_long(self):
        data = self._get_valid_data()
        data["url"] = "http://example.com/" + ("repeat" * 200)
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["URL too long (max 936 characters)"]}, f.errors)

    def test_invalid_url(self):
        data = self._get_valid_data()
        data["url"] = "ttp://example.com"
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"url": ["Invalid URL"]}, f.errors)

    def test_no_unneeded_fields(self):
        data = self._get_valid_data()
        f = forms.AdTagForm(self.campaign, data)
        self.assertTrue(f.is_valid())
        self.assertEqual("center", f.cleaned_data["image_crop"])
        self.assertEqual("", f.cleaned_data["brand_name"])
        self.assertEqual("", f.cleaned_data["description"])
        self.assertEqual(constants.DEFAULT_CALL_TO_ACTION, f.cleaned_data["call_to_action"])
        self.assertEqual(None, f.cleaned_data["additional_data"])

    def test_empty_unneeded_fields(self):
        data = self._get_valid_data()
        data["image_url"] = ""
        data["image_crop"] = ""
        data["brand_name"] = ""
        data["description"] = ""
        data["call_to_action"] = ""
        data["additional_data"] = None
        f = forms.AdTagForm(self.campaign, data)
        self.assertTrue(f.is_valid())
        self.assertEqual(None, f.cleaned_data["image_url"])
        self.assertEqual("center", f.cleaned_data["image_crop"])
        self.assertEqual("", f.cleaned_data["brand_name"])
        self.assertEqual("", f.cleaned_data["description"])
        self.assertEqual(constants.DEFAULT_CALL_TO_ACTION, f.cleaned_data["call_to_action"])
        self.assertEqual(None, f.cleaned_data["additional_data"])

    def test_http_primary_tracker(self):
        data = self._get_valid_data()
        data["primary_tracker_url"] = "http://zemanta.com/"
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"primary_tracker_url": ["Impression tracker URLs have to be HTTPS"]}, f.errors)

    def test_http_secondary_tracker(self):
        data = self._get_valid_data()
        data["secondary_tracker_url"] = "http://zemanta.com/"
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"secondary_tracker_url": ["Impression tracker URLs have to be HTTPS"]}, f.errors)

    def test_unicode_primary_tracker(self):
        data = self._get_valid_data()
        data["primary_tracker_url"] = "https://zemanta.com/š"
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"primary_tracker_url": ["Invalid impression tracker URL"]}, f.errors)

    def test_unicode_secondary_tracker(self):
        data = self._get_valid_data()
        data["secondary_tracker_url"] = "https://zemanta.com/š"
        f = forms.AdTagForm(self.campaign, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({"secondary_tracker_url": ["Invalid impression tracker URL"]}, f.errors)

    def test_no_icon_on_ad_tag_ad(self):
        data = self._get_valid_data()
        data["icon_url"] = "http://icon.com"
        data["icon_id"] = "1234id"
        data["icon_hash"] = "1234hash"
        data["icon_file_size"] = 100000
        data["icon_status"] = constants.AsyncUploadJobStatus.OK
        f = forms.AdTagForm(self.campaign, data)
        self.assertTrue(f.is_valid())
        self.assertEqual(None, f.cleaned_data["icon_url"])
        self.assertEqual(None, f.cleaned_data["icon_id"])
        self.assertEqual(None, f.cleaned_data["icon_hash"])
        self.assertEqual(None, f.cleaned_data["icon_file_size"])
        self.assertEqual(constants.AsyncUploadJobStatus.OK, f.cleaned_data["icon_status"])


class AudienceFormTestCase(TestCase):
    fixtures = ["test_models.yaml"]

    def setUp(self):
        self.account = models.Account.objects.get(pk=1)
        self.user = User.objects.get(pk=1)

    def _get_valid_data(self):
        return {
            "name": "Test Audience",
            "pixel_id": 1,
            "ttl": 90,
            "prefill_days": 90,
            "rules": [{"type": constants.AudienceRuleType.CONTAINS, "value": "test"}],
        }

    def _expect_error(self, field_name, error_message, data):
        f = forms.AudienceForm(self.account, self.user, data)
        self.assertFalse(f.is_valid())
        self.assertEqual({field_name: [error_message]}, f.errors)

    def test_form(self):
        f = forms.AudienceForm(self.account, self.user, self._get_valid_data())
        self.assertTrue(f.is_valid())

    def test_invalid_name(self):
        data = self._get_valid_data()
        data["name"] = None
        self._expect_error("name", "Please specify audience name.", data)

        data["name"] = ""
        self._expect_error("name", "Please specify audience name.", data)

        del data["name"]
        self._expect_error("name", "Please specify audience name.", data)

        data["name"] = "a" * 128
        self._expect_error("name", "Name is too long (max 127 characters)", data)

    def test_invalid_pixel_id(self):
        data = self._get_valid_data()
        data["pixel_id"] = None
        self._expect_error("pixel_id", "Please select a pixel.", data)

        del data["pixel_id"]
        self._expect_error("pixel_id", "Please select a pixel.", data)

    def test_invalid_ttl(self):
        data = self._get_valid_data()
        data["ttl"] = None
        self._expect_error("ttl", "Please specify the user retention in days.", data)

        del data["ttl"]
        self._expect_error("ttl", "Please specify the user retention in days.", data)

        data["ttl"] = 366
        self._expect_error("ttl", "Maximum number of days is 365.", data)

    def test_invalid_prefill_days(self):
        data = self._get_valid_data()

        data["prefill_days"] = 366
        self._expect_error("prefill_days", "Maximum number of days is 365.", data)

    def test_invalid_rules(self):
        data = self._get_valid_data()
        data["rules"] = None
        self._expect_error("rules", "Please select a rule.", data)

        data["rules"] = []
        self._expect_error("rules", "Please select a rule.", data)

        del data["rules"]
        self._expect_error("rules", "Please select a rule.", data)

        data["rules"] = [{"type": None, "value": "bla"}]
        self._expect_error("rules", "Please select a type of the rule.", data)

        data["rules"] = [{"type": constants.AudienceRuleType.CONTAINS, "value": None}]
        self._expect_error("rules", "Please enter conditions for the audience.", data)

        data["rules"] = [{"type": constants.AudienceRuleType.STARTS_WITH, "value": None}]
        self._expect_error("rules", "Please enter conditions for the audience.", data)

        data["rules"] = [{"type": constants.AudienceRuleType.STARTS_WITH, "value": ["foo.com"]}]
        self._expect_error("rules", "Please enter valid URLs.", data)

    def test_valid_visit_rule(self):
        data = self._get_valid_data()
        data["rules"] = [{"type": constants.AudienceRuleType.VISIT, "value": None}]
        f = forms.AudienceForm(self.account, self.user, data)
        self.assertTrue(f.is_valid())


class PublisherTargetingFormTestCase(TestCase):
    fixtures = ["test_models.yaml"]

    def setUp(self):
        self.account = models.Account.objects.get(pk=1)
        self.user = User.objects.get(pk=2)

    def test_form(self):
        f = forms.PublisherTargetingForm(
            self.user,
            {
                "entries": [
                    {"publisher": "cnn.com", "source": None, "include_subdomains": False},
                    {"publisher": "cnn2.com", "source": 1, "include_subdomains": True},
                ],
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "ad_group": 1,
            },
        )

        self.assertTrue(f.is_valid())
        self.assertEqual(
            f.cleaned_data,
            {
                "entries": [
                    {"publisher": "cnn.com", "source": None, "include_subdomains": False, "placement": None},
                    {
                        "publisher": "cnn2.com",
                        "source": models.Source.objects.get(pk=1),
                        "include_subdomains": True,
                        "placement": None,
                    },
                ],
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "ad_group": models.AdGroup.objects.get(pk=1),
                "campaign": None,
                "account": None,
                "level": "",
            },
        )

    def test_form_level(self):
        f = forms.PublisherTargetingForm(
            self.user,
            {
                "entries": [],
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "ad_group": 1,
                "level": constants.PublisherBlacklistLevel.CAMPAIGN,
            },
        )

        self.assertTrue(f.is_valid())
        self.assertDictContainsSubset(
            {
                "ad_group": None,
                "campaign": models.Campaign.objects.get(pk=1),
                "account": None,
                "level": constants.PublisherBlacklistLevel.CAMPAIGN,
            },
            f.cleaned_data,
        )

    def test_form_placement_invalid(self):
        f = forms.PublisherTargetingForm(
            self.user,
            {
                "entries": [
                    {"publisher": "", "placement": "", "source": None, "include_subdomains": False},
                    {"publisher": "", "placement": "", "source": 1, "include_subdomains": True},
                ],
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "ad_group": 1,
            },
        )

        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors["entries"], ["This field is required."])

    def test_form_placement(self):
        f = forms.PublisherTargetingForm(
            self.user,
            {
                "entries": [
                    {"publisher": "cnn.com", "placement": "widget1", "source": None, "include_subdomains": False},
                    {"publisher": "cnn2.com", "placement": "widget1", "source": 1, "include_subdomains": True},
                ],
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "ad_group": 1,
            },
        )

        self.assertTrue(f.is_valid())
        self.assertEqual(
            f.cleaned_data,
            {
                "entries": [
                    {"publisher": "cnn.com", "source": None, "placement": "widget1", "include_subdomains": False},
                    {
                        "publisher": "cnn2.com",
                        "placement": "widget1",
                        "source": models.Source.objects.get(pk=1),
                        "include_subdomains": True,
                    },
                ],
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "ad_group": models.AdGroup.objects.get(pk=1),
                "campaign": None,
                "account": None,
                "level": "",
            },
        )

    def test_form_missing_placement(self):
        f = forms.PublisherTargetingForm(
            self.user,
            {
                "entries": [
                    {"publisher": "cnn.com", "source": None, "include_subdomains": False},
                    {"publisher": "cnn2.com", "source": 1, "include_subdomains": True},
                ],
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "ad_group": 1,
            },
        )

        self.assertTrue(f.is_valid())
        self.assertEqual(
            f.cleaned_data,
            {
                "entries": [
                    {"publisher": "cnn.com", "source": None, "placement": None, "include_subdomains": False},
                    {
                        "publisher": "cnn2.com",
                        "placement": None,
                        "source": models.Source.objects.get(pk=1),
                        "include_subdomains": True,
                    },
                ],
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "ad_group": models.AdGroup.objects.get(pk=1),
                "campaign": None,
                "account": None,
                "level": "",
            },
        )

    def test_form_empty_placement(self):
        f = forms.PublisherTargetingForm(
            self.user,
            {
                "entries": [
                    {"publisher": "cnn.com", "placement": "", "source": None, "include_subdomains": False},
                    {"publisher": "cnn2.com", "placement": "", "source": 1, "include_subdomains": True},
                ],
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "ad_group": 1,
            },
        )

        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors["entries"], ["Placement must not be empty"])

    def test_form_not_reported_placement(self):
        f = forms.PublisherTargetingForm(
            self.user,
            {
                "entries": [
                    {"publisher": "cnn.com", "placement": "Not reported", "source": None, "include_subdomains": False},
                    {"publisher": "cnn2.com", "placement": "Not reported", "source": 1, "include_subdomains": True},
                ],
                "status": constants.PublisherTargetingStatus.BLACKLISTED,
                "ad_group": 1,
            },
        )

        self.assertFalse(f.is_valid())
        self.assertEqual(f.errors["entries"], ['Invalid placement: "Not reported"'])
