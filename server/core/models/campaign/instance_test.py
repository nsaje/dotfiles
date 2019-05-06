from django.test import TestCase

from utils.magic_mixer import magic_mixer

from .model import Campaign


class TestCampaignInstance(TestCase):
    def test_archive_restore(self):
        request = magic_mixer.blend_request_user()
        campaign = magic_mixer.blend(Campaign)
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)
        campaign.archive(request)
        self.assertTrue(campaign.archived)
        self.assertTrue(campaign.settings.archived)
        campaign.restore(request)
        self.assertFalse(campaign.archived)
        self.assertFalse(campaign.settings.archived)
