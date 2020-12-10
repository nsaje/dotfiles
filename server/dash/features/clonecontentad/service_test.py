from django.test import TestCase
from mock import patch

import core.models
import core.models.content_ad.exceptions
import dash.constants
from core.models.account.exceptions import AccountDoesNotMatch
from utils.magic_mixer import magic_mixer

from . import service


class Clone(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.source_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        icon = magic_mixer.blend(
            core.models.ImageAsset,
            hash="iconhash",
            width=200,
            height=200,
            file_size=1000,
            origin_url="http://origin.url.com",
        )
        self.source_content_ads = magic_mixer.cycle(5).blend(
            core.models.ContentAd, ad_group=self.source_ad_group, icon=icon
        )
        magic_mixer.cycle(3).blend(
            core.features.bid_modifiers.models.BidModifier,
            ad_group=self.source_ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.AD,
            target=(str(ad.id) for ad in self.source_content_ads[:3]),
            modifier=1.2,
        )
        self.request = magic_mixer.blend_request_user()

    @patch("utils.sspd_client.sync_batch", autospec=True)
    @patch("utils.k1_helper.update_ad_group", autospec=True)
    def test_clone(self, mock_update_ad_group, mock_sspd_sync):
        batch = service.clone(self.request, self.source_ad_group, self.source_content_ads, self.ad_group)

        cloned_ads = core.models.ContentAd.objects.filter(batch=batch)

        source_ads_dicts = [x.to_cloned_candidate_dict() for x in self.source_content_ads]
        cloned_ads_dicts = [x.to_cloned_candidate_dict() for x in cloned_ads]

        for i in range(len(source_ads_dicts)):
            del source_ads_dicts[i]["original_content_ad_id"]
            del cloned_ads_dicts[i]["original_content_ad_id"]

        self.assertCountEqual(source_ads_dicts, cloned_ads_dicts)
        source_icon = self.source_content_ads[0].icon
        cloned_icon = cloned_ads[0].icon
        self.assertEqual(source_icon.image_id, cloned_icon.image_id)
        self.assertEqual(source_icon.image_hash, cloned_icon.image_hash)
        self.assertEqual(source_icon.width, cloned_icon.height)
        self.assertEqual(source_icon.height, cloned_icon.height)
        self.assertEqual(source_icon.file_size, cloned_icon.file_size)
        self.assertEqual(source_icon.origin_url, cloned_icon.origin_url)
        self.assertEqual(1, core.models.ImageAsset.objects.all().count())

        self.assertEqual(batch.ad_group, self.ad_group)
        mock_update_ad_group.assert_called_with(batch.ad_group, msg="clonecontent.clone")
        mock_sspd_sync.assert_called_with(batch)

        self.assertEqual(
            [content_ad.state for content_ad in self.source_content_ads],
            [cloned_content_ad.state for cloned_content_ad in cloned_ads],
        )

        bid_modifiers = core.features.bid_modifiers.BidModifier.objects.filter(
            ad_group=self.ad_group,
            type=core.features.bid_modifiers.constants.BidModifierType.AD,
            target__in=[str(ad.id) for ad in cloned_ads],
        )
        self.assertEqual(3, len(bid_modifiers))
        for bid_modifier in bid_modifiers:
            self.assertEqual(1.2, bid_modifier.modifier)

    def test_clone_state_override(self):
        for content_ad in self.source_content_ads:
            self.assertEqual(content_ad.state, dash.constants.ContentAdSourceState.ACTIVE)

        batch = service.clone(
            self.request,
            self.source_ad_group,
            self.source_content_ads,
            self.ad_group,
            state_override=dash.constants.ContentAdSourceState.INACTIVE,
        )

        cloned_ads = core.models.ContentAd.objects.filter(batch=batch)

        for content_ad in cloned_ads:
            self.assertEqual(content_ad.state, dash.constants.ContentAdSourceState.INACTIVE)

    def test_clone_type_mismatch(self):
        self.ad_group.campaign.type = dash.constants.CampaignType.VIDEO
        self.ad_group.campaign.save(None)
        with self.assertRaises(core.models.content_ad.exceptions.CampaignAdTypeMismatch):
            service.clone(self.request, self.source_ad_group, self.source_content_ads, self.ad_group)

    def test_validate_other_account(self):
        other_account = magic_mixer.blend(core.models.Account)
        other_campaign = magic_mixer.blend(core.models.Campaign, account=other_account)
        other_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=other_campaign)

        try:
            service.clone(self.request, self.source_ad_group, self.source_content_ads, other_ad_group)
            self.fail("Cloned into a different account")
        except AccountDoesNotMatch as exc:
            self.assertEqual(exc.errors, {"account": "Can not clone into a different account"})
