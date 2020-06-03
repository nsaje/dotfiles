from django.conf import settings
from django.test import TestCase
from django.test import override_settings
from mock import patch

import core.models
from dash import constants
from utils.magic_mixer import magic_mixer

from . import exceptions


@patch("core.models.ContentAd.objects.insert_redirects")
class CreateContentAd(TestCase):
    def test_create(self, mock_insert_redirects):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        batch = magic_mixer.blend(core.models.UploadBatch, ad_group=ad_group)
        sources = magic_mixer.cycle(5).blend(core.models.Source)

        content_ad = core.models.ContentAd.objects.create(batch, sources, url="zemanta.com", brand_name="Zemanta")

        self.assertEqual(content_ad.batch, batch)
        self.assertEqual(content_ad.url, "zemanta.com")
        self.assertEqual(content_ad.brand_name, "Zemanta")

        self.assertEqual(content_ad.contentadsource_set.all().count(), 5)
        mock_insert_redirects.assert_called_with([content_ad], clickthrough_resolve=True)

    def test_create_icon(self, mock_insert_redirects):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        batch = magic_mixer.blend(core.models.UploadBatch, ad_group=ad_group)
        sources = magic_mixer.cycle(5).blend(core.models.Source)
        icon = magic_mixer.blend(core.models.ImageAsset, image_id="icon", width=200, height=200)
        content_ad_1 = core.models.ContentAd.objects.create(
            batch, sources, icon_id=None, icon_hash=None, icon_height=None, icon_width=None, icon_file_size=None
        )
        content_ad_2 = core.models.ContentAd.objects.create(batch, sources, icon=icon)
        content_ad_3 = core.models.ContentAd.objects.create(
            batch, sources, icon_id="icon2", icon_hash="hash", icon_width=100, icon_height=100, icon_file_size=1000
        )
        content_ad_4 = core.models.ContentAd.objects.create(
            batch,
            sources,
            icon_id="icon3",
            icon_hash="hash",
            icon_width=300,
            icon_height=300,
            icon_file_size=1000,
            icon_url="test.com",
        )
        self.assertIsNone(content_ad_1.icon)
        self.assertEqual(200, content_ad_2.icon.width)
        self.assertEqual(200, content_ad_2.icon.height)
        self.assertEqual(100, content_ad_3.icon.width)
        self.assertEqual(100, content_ad_3.icon.height)
        self.assertIsNone(content_ad_3.icon.origin_url)
        self.assertEqual(300, content_ad_4.icon.width)
        self.assertEqual(300, content_ad_4.icon.height)
        self.assertEqual("test.com", content_ad_4.icon.origin_url)

    def test_create_ad_group_archived(self, mock_insert_redirects):
        ad_group = magic_mixer.blend(core.models.AdGroup, archived=True)
        batch = magic_mixer.blend(core.models.UploadBatch, ad_group=ad_group)
        sources = magic_mixer.cycle(5).blend(core.models.Source)
        with self.assertRaises(exceptions.AdGroupIsArchived):
            core.models.ContentAd.objects.create(batch, sources, url="zemanta.com", brand_name="Zemanta")
        mock_insert_redirects.assert_not_called()

    def test_create_icon_not_square(self, mock_insert_redirects):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        batch = magic_mixer.blend(core.models.UploadBatch, ad_group=ad_group)
        sources = magic_mixer.cycle(5).blend(core.models.Source)
        with self.assertRaises(exceptions.IconNotSquare):
            core.models.ContentAd.objects.create(batch, sources, icon_height=200, icon_width=100)
        with self.assertRaises(exceptions.IconNotSquare):
            core.models.ContentAd.objects.create(batch, sources, icon_height=200)
        with self.assertRaises(exceptions.IconNotSquare):
            core.models.ContentAd.objects.create(batch, sources, icon_width=100)
        mock_insert_redirects.assert_not_called()

    def test_create_icon_incomplete_data(self, mock_insert_redirects):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        batch = magic_mixer.blend(core.models.UploadBatch, ad_group=ad_group)
        sources = magic_mixer.cycle(5).blend(core.models.Source)
        with self.assertRaises(exceptions.IconInvalid):
            core.models.ContentAd.objects.create(
                batch,
                sources,
                icon_id="icon_id",
                icon_hash="icon_hash",
                icon_height=200,
                icon_width=200,
                icon_file_size=None,
            )
        with self.assertRaises(exceptions.IconInvalid):
            core.models.ContentAd.objects.create(
                batch, sources, icon_id="icon_id", icon_hash="icon_hash", icon_height=200, icon_width=200
            )
        with self.assertRaises(exceptions.IconInvalid):
            core.models.ContentAd.objects.create(
                batch,
                sources,
                icon_id="icon_id",
                icon_hash="icon_hash",
                icon_height=None,
                icon_width=None,
                icon_file_size=1000,
            )
        with self.assertRaises(exceptions.IconInvalid):
            core.models.ContentAd.objects.create(
                batch, sources, icon_id="icon_id", icon_hash="icon_hash", icon_file_size=1000
            )
        with self.assertRaises(exceptions.IconInvalid):
            core.models.ContentAd.objects.create(
                batch, sources, icon_id="icon_id", icon_hash=None, icon_height=200, icon_width=200, icon_file_size=1000
            )
        with self.assertRaises(exceptions.IconInvalid):
            core.models.ContentAd.objects.create(
                batch, sources, icon_id="icon_id", icon_height=200, icon_width=200, icon_file_size=1000
            )
        with self.assertRaises(exceptions.IconInvalid):
            core.models.ContentAd.objects.create(
                batch,
                sources,
                icon_id=None,
                icon_hash="icon_hash",
                icon_height=200,
                icon_width=200,
                icon_file_size=1000,
            )
        with self.assertRaises(exceptions.IconInvalid):
            core.models.ContentAd.objects.create(
                batch, sources, icon_hash="icon_hash", icon_height=200, icon_width=200, icon_file_size=1000
            )
        mock_insert_redirects.assert_not_called()
        core.models.ContentAd.objects.create(
            batch,
            sources,
            icon_id="icon_id",
            icon_hash="icon_hash",
            icon_height=200,
            icon_width=200,
            icon_file_size=1000,
        )
        mock_insert_redirects.assert_called_once()

    def _blend_a_batch(self):
        ad_group = magic_mixer.blend(core.models.AdGroup)
        sources = magic_mixer.cycle(3).blend(
            core.models.Source,
            maintenance=False,
            deprecated=False,
            source_type__available_actions=[constants.SourceAction.CAN_MANAGE_CONTENT_ADS],
        )

        for source in sources:
            # when using cycle we get random values as source, this is a workaround
            magic_mixer.blend(core.models.AdGroupSource, ad_group=ad_group, can_manage_content_ads=True, source=source)

        return magic_mixer.blend(core.models.UploadBatch, ad_group=ad_group)

    @override_settings(IMAGE_THUMBNAIL_URL="http://test.com")
    def test_bulk_create_from_candidates(self, mock_insert_redirects):
        batch = self._blend_a_batch()
        icon = magic_mixer.blend(
            core.models.ImageAsset,
            image_id="icon_id",
            image_hash="icon_hash",
            width=200,
            height=200,
            file_size=1234,
            origin_url="test.com",
        )
        candidates = [x.to_candidate_dict() for x in magic_mixer.cycle(3).blend(core.models.ContentAd, icon=icon)]
        content_ads = core.models.ContentAd.objects.bulk_create_from_candidates(candidates, batch)

        self.assertEqual(len(content_ads), 3)

        for content_ad in content_ads:
            self.assertEqual(content_ad.batch, batch)
            self.assertEqual(content_ad.ad_group, batch.ad_group)
            self.assertCountEqual(
                [x.source for x in content_ad.contentadsource_set.all()], list(batch.ad_group.sources.all())
            )
            self.assertEqual("icon_id", content_ad.icon.image_id)
            self.assertEqual("icon_hash", content_ad.icon.image_hash)
            self.assertEqual(200, content_ad.icon.width)
            self.assertEqual(200, content_ad.icon.height)
            self.assertEqual(1234, content_ad.icon.file_size)
            self.assertEqual("test.com", content_ad.icon.origin_url)

        # check redirector sync
        self.assertEqual(mock_insert_redirects.call_count, 1)
        mock_insert_redirects.assert_called_with(content_ads, clickthrough_resolve=True)

    def test_bulk_clone(self, mock_insert_redirects):
        request = magic_mixer.blend_request_user()
        batch = self._blend_a_batch()
        batch.state_override = None
        batch.save()
        icon = magic_mixer.blend(
            core.models.ImageAsset,
            image_id="icon_id",
            image_hash="icon_hash",
            width=200,
            height=200,
            file_size=1234,
            origin_url="test.com",
        )
        source_content_ads = magic_mixer.cycle(3).blend(
            core.models.ContentAd, state=constants.ContentAdSourceState.INACTIVE, icon=icon
        )

        content_ads = core.models.ContentAd.objects.bulk_clone(request, source_content_ads, batch.ad_group, batch)

        self.assertEqual(len(content_ads), 3)

        for content_ad in content_ads:
            self.assertEqual(content_ad.batch, batch)
            self.assertEqual(content_ad.state, constants.ContentAdSourceState.INACTIVE)
            self.assertEqual(content_ad.ad_group, batch.ad_group)
            self.assertCountEqual(
                [x.source for x in content_ad.contentadsource_set.all()], list(batch.ad_group.sources.all())
            )
            self.assertEqual("icon_id", content_ad.icon.image_id)
            self.assertEqual("icon_hash", content_ad.icon.image_hash)
            self.assertEqual(200, content_ad.icon.width)
            self.assertEqual(200, content_ad.icon.height)
            self.assertEqual(1234, content_ad.icon.file_size)
            self.assertEqual("test.com", content_ad.icon.origin_url)

        # check redirector sync
        self.assertEqual(mock_insert_redirects.call_count, 1)
        mock_insert_redirects.assert_called_with(content_ads, clickthrough_resolve=False)

    def test_bulk_clone_override_state(self, mock_insert_redirects):
        request = magic_mixer.blend_request_user()
        batch = self._blend_a_batch()
        batch.state_override = constants.ContentAdSourceState.ACTIVE
        batch.save()
        icon = magic_mixer.blend(
            core.models.ImageAsset,
            image_id="icon_id",
            image_hash="icon_hash",
            width=200,
            height=200,
            file_size=1234,
            origin_url="test.com",
        )
        source_content_ads = magic_mixer.cycle(3).blend(
            core.models.ContentAd, state=constants.ContentAdSourceState.INACTIVE, icon=icon
        )

        content_ads = core.models.ContentAd.objects.bulk_clone(request, source_content_ads, batch.ad_group, batch)

        self.assertEqual(len(content_ads), 3)

        for content_ad in content_ads:
            self.assertEqual(content_ad.batch, batch)
            self.assertEqual(content_ad.state, constants.ContentAdSourceState.ACTIVE)
            self.assertEqual(content_ad.ad_group, batch.ad_group)
            self.assertCountEqual(
                [x.source for x in content_ad.contentadsource_set.all()], list(batch.ad_group.sources.all())
            )
            self.assertEqual("icon_id", content_ad.icon.image_id)
            self.assertEqual("icon_hash", content_ad.icon.image_hash)
            self.assertEqual(200, content_ad.icon.width)
            self.assertEqual(200, content_ad.icon.height)
            self.assertEqual(1234, content_ad.icon.file_size)
            self.assertEqual("test.com", content_ad.icon.origin_url)

        # check redirector sync
        self.assertEqual(mock_insert_redirects.call_count, 1)
        mock_insert_redirects.assert_called_with(content_ads, clickthrough_resolve=False)

    @patch.object(core.models.AdGroup, "is_archived", return_value=True)
    def test_bulk_clone_archived_ad_group_fail(self, mock_archived, mock_insert_redirects):
        request = magic_mixer.blend_request_user()
        batch = self._blend_a_batch()
        icon = magic_mixer.blend(core.models.ImageAsset, width=200, height=200)
        source_content_ads = magic_mixer.cycle(3).blend(
            core.models.ContentAd, state=constants.ContentAdSourceState.INACTIVE, icon=icon
        )

        with self.assertRaises(exceptions.AdGroupIsArchived):
            core.models.ContentAd.objects.bulk_clone(request, source_content_ads, batch.ad_group, batch)

        # check redirector sync
        mock_insert_redirects.assert_not_called()

    @patch("django.conf.settings.HARDCODED_ACCOUNT_ID_OEN", 305)
    def test_create_oen_additional_data(self, mock_insert_redirects):
        core.models.Account.objects.filter(id=settings.HARDCODED_ACCOUNT_ID_OEN).delete()
        account = magic_mixer.blend(core.models.Account, id=settings.HARDCODED_ACCOUNT_ID_OEN)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)
        batch = magic_mixer.blend(core.models.UploadBatch, ad_group=ad_group)
        sources = magic_mixer.cycle(5).blend(core.models.Source)

        content_ad = core.models.ContentAd.objects.create(batch, sources, additional_data={"document_features": "test"})

        self.assertEqual(content_ad.document_features, {"categories": "test"})
