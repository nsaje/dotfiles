from django.test import TestCase
from django.test import override_settings

import core.models
import dash.constants
from utils.magic_mixer import magic_mixer


@override_settings(IMAGE_THUMBNAIL_URL="http://test.com")
class ContentAdCandidateInstanceTest(TestCase):
    def test_get_default_icon_hosted_url(self):
        account = magic_mixer.blend(core.models.Account)
        campaign = magic_mixer.blend(core.models.Campaign, account=account)
        campaign.settings.update_unsafe(None, iab_category=dash.constants.IABCategory.IAB10_7)
        candidate = magic_mixer.blend(
            core.models.ContentAdCandidate,
            ad_group__campaign=campaign,
            icon_url="http://icon.url.com",
            icon_id=None,
            original_content_ad=None,
        )

        icon_url = candidate.get_hosted_icon_url()
        self.assertIsNone(icon_url)

        candidate.icon_url = None

        icon_url = candidate.get_hosted_icon_url()
        self.assertEqual("http://test.com/d/icons/IAB10.jpg", icon_url)
        icon_url = candidate.get_hosted_icon_url(700)
        self.assertEqual("http://test.com/d/icons/IAB10.jpg?w=700&h=700&fit=crop&crop=center", icon_url)

        default_icon = magic_mixer.blend(core.models.ImageAsset, image_id="account_icon_id", width=300, height=300)
        account.settings.update_unsafe(None, default_icon=default_icon)
        icon_url = candidate.get_hosted_icon_url()
        self.assertEqual("http://test.com/account_icon_id.jpg?w=300&h=300&fit=crop&crop=center", icon_url)
        icon_url = candidate.get_hosted_icon_url(800)
        self.assertEqual("http://test.com/account_icon_id.jpg?w=800&h=800&fit=crop&crop=center", icon_url)

        candidate.icon_id = "candidate_icon_id"
        candidate.icon_width = 200
        candidate.icon_height = 200
        icon_url = candidate.get_hosted_icon_url()
        self.assertEqual("http://test.com/candidate_icon_id.jpg?w=200&h=200&fit=crop&crop=center", icon_url)
        icon_url = candidate.get_hosted_icon_url(900)
        self.assertEqual("http://test.com/candidate_icon_id.jpg?w=900&h=900&fit=crop&crop=center", icon_url)
