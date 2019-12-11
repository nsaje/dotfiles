from django.test import TestCase
from django.test import override_settings

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer


@override_settings(IMAGE_THUMBNAIL_URL="http://test.com")
class ModelHelpersTest(TestCase):
    def test_get_hosted_default_icon_url(self):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        campaign.settings.update_unsafe(None, iab_category=dash.constants.IABCategory.IAB10_7)

        candidate = magic_mixer.blend(
            core.models.ContentAdCandidate, ad_group__campaign=campaign, icon_id=None, original_content_ad=None
        )
        icon_url = core.models.helpers.get_hosted_default_icon_url(candidate)
        self.assertEqual("http://test.com/d/icons/IAB10.jpg", icon_url)
        icon_url = core.models.helpers.get_hosted_default_icon_url(candidate, 700)
        self.assertEqual("http://test.com/d/icons/IAB10.jpg?w=700&h=700&fit=crop&crop=center", icon_url)

        default_icon = magic_mixer.blend(core.models.ImageAsset, image_id="account_icon_id", width=300, height=300)
        account.settings.update_unsafe(None, default_icon=default_icon)
        content_ad = magic_mixer.blend(
            core.models.ContentAd, ad_group__campaign=campaign, icon_id=None, original_content_ad=None
        )
        icon_url = core.models.helpers.get_hosted_default_icon_url(content_ad)
        self.assertEqual("http://test.com/d/icons/IAB10.jpg", icon_url)
        icon_url = core.models.helpers.get_hosted_default_icon_url(content_ad, 700)
        self.assertEqual("http://test.com/d/icons/IAB10.jpg?w=700&h=700&fit=crop&crop=center", icon_url)
