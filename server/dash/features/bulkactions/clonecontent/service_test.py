from django.test import TestCase
from mock import patch

import core.models
from core.models.account.exceptions import AccountDoesNotMatch
from utils.magic_mixer import magic_mixer

from . import service


@patch.object(core.models.ContentAd.objects, "insert_redirects", autospec=True)
class Clone(TestCase):
    def setUp(self):
        self.account = magic_mixer.blend(core.models.Account)
        self.campaign = magic_mixer.blend(core.models.Campaign, account=self.account)
        self.source_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.ad_group = magic_mixer.blend(core.models.AdGroup, campaign=self.campaign)
        self.source_content_ads = magic_mixer.cycle(5).blend(core.models.ContentAd, ad_group=self.source_ad_group)
        self.request = magic_mixer.blend_request_user()

    def test_clone(self, _):
        batch = service.clone(self.request, self.source_ad_group, self.source_content_ads, self.ad_group)

        self.assertCountEqual(
            [x.to_cloned_candidate_dict() for x in self.source_content_ads],
            [x.to_cloned_candidate_dict() for x in core.models.ContentAd.objects.filter(batch=batch)],
        )

        self.assertEqual(batch.ad_group, self.ad_group)

    def test_validate_other_account(self, _):
        other_account = magic_mixer.blend(core.models.Account)
        other_campaign = magic_mixer.blend(core.models.Campaign, account=other_account)
        other_ad_group = magic_mixer.blend(core.models.AdGroup, campaign=other_campaign)

        try:
            service.clone(self.request, self.source_ad_group, self.source_content_ads, other_ad_group)
            self.fail("Cloned into a different account")
        except AccountDoesNotMatch as exc:
            self.assertEqual(exc.errors, {"account": "Can not clone into a different account"})
