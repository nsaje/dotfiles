import mock
from django.test import TestCase

import core.models
from core.features import bid_modifiers
from core.features.bid_modifiers import exceptions
from dash import models
from utils.magic_mixer import magic_mixer

from . import service


def add_non_publisher_bid_modifiers(**kwargs):
    """Add some non publisher bid modifiers that should not alter test results."""

    blend_kwargs = {
        "publisher": ("somerandompub%s.com" % i for i in range(7)),
        "modifier": 0.5,
        "type": (
            t
            for t in (
                bid_modifiers.constants.BidModifierType.SOURCE,
                bid_modifiers.constants.BidModifierType.DEVICE,
                bid_modifiers.constants.BidModifierType.OPERATING_SYSTEM,
                bid_modifiers.constants.BidModifierType.PLACEMENT,
                bid_modifiers.constants.BidModifierType.COUNTRY,
                bid_modifiers.constants.BidModifierType.STATE,
                bid_modifiers.constants.BidModifierType.DMA,
            )
        ),
    }
    blend_kwargs.update(kwargs)
    if "source" in blend_kwargs:
        blend_kwargs["source_slug"] = blend_kwargs["source"].bidder_slug

    magic_mixer.cycle(7).blend(bid_modifiers.BidModifier, **blend_kwargs)


@mock.patch("utils.k1_helper.update_ad_group", mock.MagicMock())
class TestPublisherBidModifierService(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(core.models.AdGroup)
        self.source = magic_mixer.blend(core.models.Source, bidder_slug="some_slug")

        add_non_publisher_bid_modifiers(ad_group=self.ad_group, source=self.source)

    def _create(self, modifier, publisher="testpub"):
        bid_modifiers.BidModifier.publisher_objects.create(
            ad_group=self.ad_group,
            source=self.source,
            source_slug=self.source.bidder_slug,
            target=publisher,
            modifier=modifier,
            type=bid_modifiers.constants.BidModifierType.PUBLISHER,
        )

    def test_get(self):
        self._create(0.5, "testpub1")
        self._create(4.6, "testpub2")
        self.assertEqual(
            service.get(self.ad_group),
            [
                {"publisher": "testpub1", "source": self.source, "modifier": 0.5},
                {"publisher": "testpub2", "source": self.source, "modifier": 4.6},
            ],
        )

    def test_set_nonexisting(self):
        service.set(self.ad_group, "testpub", self.source, 1.2)
        actual = bid_modifiers.BidModifier.publisher_objects.get(
            ad_group=self.ad_group, source=self.source, target="testpub"
        ).modifier
        self.assertEqual(1.2, actual)

    def test_set_existing(self):
        self._create(0.5)

        service.set(self.ad_group, "testpub", self.source, 1.2)

        self.assertEqual(
            bid_modifiers.BidModifier.publisher_objects.filter(
                ad_group=self.ad_group, source=self.source, target="testpub"
            ).count(),
            1,
        )

        actual = bid_modifiers.BidModifier.publisher_objects.get(
            ad_group=self.ad_group, source=self.source, target="testpub"
        ).modifier
        self.assertEqual(1.2, actual)

    def test_set_none(self):
        self._create(0.5)

        service.set(self.ad_group, "testpub", self.source, None)

        count = bid_modifiers.BidModifier.publisher_objects.filter(
            ad_group=self.ad_group, source=self.source, target="testpub"
        ).count()
        self.assertEqual(0, count)

    def test_set_1(self):
        self._create(0.5)

        service.set(self.ad_group, "testpub", self.source, 1.0)

        actual = bid_modifiers.BidModifier.publisher_objects.get(
            ad_group=self.ad_group, source=self.source, target="testpub"
        ).modifier
        self.assertEqual(1.0, actual)

    def test_set_invalid(self):
        self._create(0.5)

        with self.assertRaises(exceptions.BidModifierInvalid):
            service.set(self.ad_group, "testpub", self.source, "wth?")

        with self.assertRaises(exceptions.BidModifierInvalid):
            service.set(self.ad_group, "testpub", self.source, 35)

    def test__clean_bid_modifier(self):
        modifier = "ASD"
        errors = []
        self.assertEqual(service._clean_bid_modifier(modifier, errors), None)
        self.assertEqual(errors, ["Invalid Bid Modifier"])

        modifier = 0.0
        errors = []
        self.assertEqual(service._clean_bid_modifier(modifier, errors), 0.0)
        self.assertEqual(errors, ["Bid modifier too low (< 0.01)"])

        modifier = 1.0
        errors = []
        self.assertEqual(service._clean_bid_modifier(modifier, errors), None)
        self.assertEqual(errors, [])

    def test__clean_source_slug(self):
        source_slug = "bad slug"
        sources_by_slug = {x.get_clean_slug(): x for x in models.Source.objects.all()}
        errors = []
        self.assertEqual(service._clean_source_slug(source_slug, sources_by_slug, errors), None)
        self.assertEqual(errors, ["Invalid Source Slug"])

        source_slug = "some_slug"
        errors = []
        self.assertEqual(service._clean_source_slug(source_slug, sources_by_slug, errors), self.source)
        self.assertEqual(errors, [])

    def test__clean_publisher(self):
        publisher = "http://example.com"
        errors = []
        self.assertEqual(service._clean_publisher(publisher, errors), "example.com")
        self.assertEqual(errors, ["Remove the following prefixes: http, https"])

        publisher = "https://example.com/"
        errors = []
        self.assertEqual(service._clean_publisher(publisher, errors), "example.com")
        self.assertEqual(errors, ["Remove the following prefixes: http, https", "Publisher should not contain /"])

    def test_clean_entries(self):
        entries = [
            {"Publisher": "all publishers", "Source Slug": "some_slug", "Bid Modifier": ""},
            {"Publisher": "example1.com", "Source Slug": "some_slug", "Bid Modifier": 1.0},
            {"Publisher": "example2.com", "Source Slug": "some_slug", "Bid Modifier": 2.1},
        ]
        test_entries = entries.copy()
        cleaned_entries, error = service.clean_entries(entries)
        self.assertEqual(error, False)
        self.assertEqual(
            cleaned_entries,
            [
                {"publisher": "example1.com", "modifier": None, "source": self.source},
                {"publisher": "example2.com", "modifier": 2.1, "source": self.source},
            ],
        )
        self.assertEqual(entries, test_entries)

        entries = [
            {"Publisher": "https://example.com", "Source Slug": "bad_slug", "Bid Modifier": 12.0},
            {"Publisher": "example2.com/", "Source Slug": "some_slug", "Bid Modifier": 0.0},
            {"Publisher": "example3.com", "Source Slug": "some_slug", "Bid Modifier": "ASD"},
            {"Publisher": "all publishers", "Source Slug": "some_slug", "Bid Modifier": 2.0},
        ]
        cleaned_entries, error = service.clean_entries(entries)
        self.assertEqual(error, True)
        self.assertEqual(
            entries[0]["Errors"],
            "Bid modifier too high (> 11.0); Invalid Source Slug; Remove the following prefixes: http, https",
        )
        self.assertEqual(entries[1]["Errors"], "Bid modifier too low (< 0.01); Publisher should not contain /")
        self.assertEqual(entries[2]["Errors"], "Invalid Bid Modifier")
        self.assertEqual(entries[3]["Errors"], "'all publishers' can not have a bid modifier set")
