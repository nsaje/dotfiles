from django.test import TestCase

import core.models
from dash import constants
from utils.magic_mixer import magic_mixer

from . import exceptions


class ValidationTestCase(TestCase):
    def test_campaign_type_mismatch_content(self):
        campaign = magic_mixer.blend(core.models.Campaign, type=constants.CampaignType.CONTENT)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group, type=constants.AdType.CONTENT)
        content_ad.save()

        campaign.type = constants.CampaignType.CONVERSION
        campaign.save(None)
        content_ad.save()

        campaign.type = constants.CampaignType.MOBILE
        campaign.save(None)
        content_ad.save()

        with self.assertRaises(exceptions.CampaignAdTypeMismatch):
            content_ad.type = constants.AdType.IMAGE
            content_ad.save()

    def test_campaign_type_mismatch_video(self):
        campaign = magic_mixer.blend(core.models.Campaign, type=constants.CampaignType.VIDEO)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group, type=constants.AdType.VIDEO)
        content_ad.save()

        with self.assertRaises(exceptions.CampaignAdTypeMismatch):
            content_ad.type = constants.AdType.CONTENT
            content_ad.save()

    def test_campaign_type_mismatch_display(self):
        campaign = magic_mixer.blend(core.models.Campaign, type=constants.CampaignType.DISPLAY)
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign=campaign)
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group=ad_group, type=constants.AdType.IMAGE)
        content_ad.save()

        content_ad.type = constants.AdType.AD_TAG
        content_ad.save()

        with self.assertRaises(exceptions.CampaignAdTypeMismatch):
            content_ad.type = constants.AdType.VIDEO
            content_ad.save()
