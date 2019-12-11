from django.test import TestCase
from django.test import override_settings

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer

from . import model


@override_settings(IMAGE_THUMBNAIL_URL="http://test.com")
class ContentAdModelTest(TestCase):
    def test_get_hosted_icon_url(self):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        campaign.settings.update_unsafe(None, iab_category=dash.constants.IABCategory.IAB16_3)
        ad = magic_mixer.blend(model.ContentAd, ad_group__campaign=campaign, icon_id=None)
        icon_url = ad.get_hosted_icon_url()
        self.assertEqual("http://test.com/d/icons/IAB16.jpg", icon_url)
        icon_url = ad.get_hosted_icon_url(700)
        self.assertEqual("http://test.com/d/icons/IAB16.jpg?w=700&h=700&fit=crop&crop=center", icon_url)

        default_icon = magic_mixer.blend(core.models.ImageAsset, image_id="account_icon_id", width=300, height=300)
        account.settings.update_unsafe(None, default_icon=default_icon)
        icon_url = ad.get_hosted_icon_url()
        self.assertEqual("http://test.com/account_icon_id.jpg?w=300&h=300&fit=crop&crop=center", icon_url)
        icon_url = ad.get_hosted_icon_url(800)
        self.assertEqual("http://test.com/account_icon_id.jpg?w=800&h=800&fit=crop&crop=center", icon_url)

        ad.icon = magic_mixer.blend(core.models.ImageAsset, image_id="ad_icon_id", width=200, height=200)
        icon_url = ad.get_hosted_icon_url()
        self.assertEqual("http://test.com/ad_icon_id.jpg?w=200&h=200&fit=crop&crop=center", icon_url)
        icon_url = ad.get_hosted_icon_url(900)
        self.assertEqual("http://test.com/ad_icon_id.jpg?w=900&h=900&fit=crop&crop=center", icon_url)
