import uuid

from django.test import TestCase

import core.features.creatives
import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from . import service


class ServiceTestCase(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)

    def test_migrate_for_account(self):
        ad = magic_mixer.blend(
            core.models.ContentAd,
            ad_group__campaign__account=self.account,
            type=dash.constants.AdType.CONTENT,
            url="http://test.com",
            title="Test title",
            display_url="http://test.com",
            brand_name="Test name",
            description="Test description",
            call_to_action="Test action",
            image_id=uuid.uuid4(),
            image_hash="123456",
            image_width=256,
            image_height=256,
            image_file_size=256,
            image_crop=dash.constants.ImageCrop.CENTER,
        )
        service.migrate_for_account(self.account.id)

        creatives = list(core.features.creatives.Creative.objects.filter(account_id=self.account.id).all())

        self.assertEqual(len(creatives), 1)

        self.assertEqual(creatives[0].account, self.account)
        self.assertEqual(creatives[0].type, ad.type)
        self.assertEqual(creatives[0].url, ad.url)
        self.assertEqual(creatives[0].title, ad.title)
        self.assertEqual(creatives[0].display_url, ad.display_url)
        self.assertEqual(creatives[0].brand_name, ad.brand_name)
        self.assertEqual(creatives[0].description, ad.description)
        self.assertEqual(creatives[0].call_to_action, ad.call_to_action)

        self.assertIsNotNone(creatives[0].image)
        self.assertEqual(creatives[0].image.image_id, ad.image_id)
        self.assertEqual(creatives[0].image.image_hash, ad.image_hash)
        self.assertEqual(creatives[0].image.width, ad.image_width)
        self.assertEqual(creatives[0].image.height, ad.image_height)
        self.assertEqual(creatives[0].image.file_size, ad.image_file_size)
        self.assertEqual(creatives[0].image_crop, ad.image_crop)

        self.assertEqual(creatives[0].icon, ad.icon)
        self.assertEqual(creatives[0].video_asset, ad.video_asset)

        self.assertEqual(creatives[0].ad_tag, ad.ad_tag)
        self.assertEqual(creatives[0].trackers, ad.trackers)
        self.assertEqual(creatives[0].additional_data, ad.additional_data)
