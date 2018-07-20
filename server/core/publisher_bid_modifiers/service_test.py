from django.test import TestCase

import core.entity
from utils.magic_mixer import magic_mixer

from .publisher_bid_modifier import PublisherBidModifier
from . import service
from . import exceptions


class TestPublisherBidModifierService(TestCase):
    def setUp(self):
        self.ad_group = magic_mixer.blend(core.entity.AdGroup)
        self.source = magic_mixer.blend_source_w_defaults()

    def _create(self, modifier, publisher="testpub"):
        PublisherBidModifier.objects.create(
            ad_group=self.ad_group, source=self.source, publisher=publisher, modifier=modifier
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
        actual = PublisherBidModifier.objects.get(
            ad_group=self.ad_group, source=self.source, publisher="testpub"
        ).modifier
        self.assertEqual(1.2, actual)

    def test_set_existing(self):
        self._create(0.5)

        service.set(self.ad_group, "testpub", self.source, 1.2)

        actual = PublisherBidModifier.objects.get(
            ad_group=self.ad_group, source=self.source, publisher="testpub"
        ).modifier
        self.assertEqual(1.2, actual)

    def test_set_none(self):
        self._create(0.5)

        service.set(self.ad_group, "testpub", self.source, None)

        count = PublisherBidModifier.objects.filter(
            ad_group=self.ad_group, source=self.source, publisher="testpub"
        ).count()
        self.assertEqual(0, count)

    def test_set_1(self):
        self._create(0.5)

        service.set(self.ad_group, "testpub", self.source, 1.0)

        actual = PublisherBidModifier.objects.get(
            ad_group=self.ad_group, source=self.source, publisher="testpub"
        ).modifier
        self.assertEqual(1.0, actual)

    def test_set_invalid(self):
        self._create(0.5)

        with self.assertRaises(exceptions.BidModifierInvalid):
            service.set(self.ad_group, "testpub", self.source, "wth?")

        with self.assertRaises(exceptions.BidModifierInvalid):
            service.set(self.ad_group, "testpub", self.source, 35)
