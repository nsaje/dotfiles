from django.test import TestCase
from utils.magic_mixer import magic_mixer

from dash.dashapi import loaders, augmenter
from dash import models

from core.publisher_bid_modifiers import PublisherBidModifier


class PublisherAugmenterTest(TestCase):
    def setUp(self):
        ad_group = magic_mixer.blend(models.AdGroup, id=1)
        source = magic_mixer.blend(models.Source, id=1)
        magic_mixer.blend(PublisherBidModifier, ad_group=ad_group, source=source, publisher="pub1.com", modifier=0.5)
        user = magic_mixer.blend_user()

        self.bid_modifier_loader = loaders.PublisherBidModifierLoader(
            models.AdGroup.objects.all().first(),
            models.PublisherGroupEntry.objects.filter(),
            models.PublisherGroupEntry.objects.all(),
            {},
            models.Source.objects.all(),
            user,
        )

        self.augmenter = augmenter.get_augmenter_for_dimension("publisher_id")

    def test_augmenter_bid_modifiers(self):
        row = {"publisher_id": "pub1.com__1", "source_id": 1}
        self.augmenter([row], self.bid_modifier_loader)
        self.assertEquals(row["bid_modifier"], 0.5)
