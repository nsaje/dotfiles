from django.test import TestCase
from mock import patch

import core.models
from dash import constants
from utils.magic_mixer import magic_mixer


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

    def test_bulk_create_from_candidates(self, mock_insert_redirects):
        batch = self._blend_a_batch()
        candidates = [x.to_candidate_dict() for x in magic_mixer.cycle(3).blend(core.models.ContentAd)]

        content_ads = core.models.ContentAd.objects.bulk_create_from_candidates(candidates, batch)

        self.assertEqual(len(content_ads), 3)

        for content_ad in content_ads:
            self.assertEqual(content_ad.batch, batch)
            self.assertEqual(content_ad.ad_group, batch.ad_group)
            self.assertCountEqual(
                [x.source for x in content_ad.contentadsource_set.all()], list(batch.ad_group.sources.all())
            )

        # check redirector sync
        self.assertEqual(mock_insert_redirects.call_count, 1)
        mock_insert_redirects.assert_called_with(content_ads, clickthrough_resolve=True)

    @patch("utils.k1_helper.update_ad_group", autospec=True)
    def test_bulk_clone(self, mock_update_ad_group, mock_insert_redirects):
        request = magic_mixer.blend_request_user()
        batch = self._blend_a_batch()
        source_content_ads = magic_mixer.cycle(3).blend(
            core.models.ContentAd, state=constants.ContentAdSourceState.INACTIVE
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

        # check redirector sync
        self.assertEqual(mock_insert_redirects.call_count, 1)
        mock_insert_redirects.assert_called_with(content_ads, clickthrough_resolve=False)
        mock_update_ad_group.assert_called_with(batch.ad_group, msg="ContentAdManager.bulk_clone")

    @patch("utils.k1_helper.update_ad_group", autospec=True)
    def test_bulk_clone_override_state(self, mock_update_ad_group, mock_insert_redirects):
        request = magic_mixer.blend_request_user()
        batch = self._blend_a_batch()
        source_content_ads = magic_mixer.cycle(3).blend(
            core.models.ContentAd, state=constants.ContentAdSourceState.INACTIVE
        )

        content_ads = core.models.ContentAd.objects.bulk_clone(
            request, source_content_ads, batch.ad_group, batch, overridden_state=constants.ContentAdSourceState.ACTIVE
        )

        self.assertEqual(len(content_ads), 3)

        for content_ad in content_ads:
            self.assertEqual(content_ad.batch, batch)
            self.assertEqual(content_ad.state, constants.ContentAdSourceState.ACTIVE)
            self.assertEqual(content_ad.ad_group, batch.ad_group)
            self.assertCountEqual(
                [x.source for x in content_ad.contentadsource_set.all()], list(batch.ad_group.sources.all())
            )

        # check redirector sync
        self.assertEqual(mock_insert_redirects.call_count, 1)
        mock_insert_redirects.assert_called_with(content_ads, clickthrough_resolve=False)
        mock_update_ad_group.assert_called_with(batch.ad_group, msg="ContentAdManager.bulk_clone")
