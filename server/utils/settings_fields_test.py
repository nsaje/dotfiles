from django.test import TestCase
from django.test.client import RequestFactory

from core import models
from utils.magic_mixer import magic_mixer
from zemauth.models import User


class CachedOneToOneFieldTest(TestCase):
    def setUp(self):
        # Create some independent object hierarchies.
        self.entity_count = 5
        self.user = magic_mixer.blend(User)
        self.request = RequestFactory().get("/")
        self.request.user = self.user

        self.agencies = magic_mixer.cycle(self.entity_count).blend(models.Agency)
        self.accounts = magic_mixer.cycle(self.entity_count).blend(models.Account, agency=(a for a in self.agencies))

        for account in self.accounts:
            account.settings.update(self.request, account=account)

        self.campaigns = magic_mixer.cycle(self.entity_count).blend(models.Campaign, account=(a for a in self.accounts))

        for campaign in self.campaigns:
            campaign.settings.update(self.request, campaign=campaign)

        self.ad_groups = magic_mixer.cycle(self.entity_count).blend(
            models.AdGroup, campaign=(c for c in self.campaigns)
        )

        for ad_group in self.ad_groups:
            ad_group.settings.update(self.request, ad_group=ad_group)

    def test_full_cache(self):
        # Make a query accross all created objects.
        ad_groups = models.AdGroup.objects.all()
        ad_groups = ad_groups.select_related(
            "settings", "campaign__settings", "campaign__account__settings", "campaign__account__agency__settings"
        )

        # A single DB query is expected.
        with self.assertNumQueries(1):
            for ad_group in ad_groups:
                initial_id = id(ad_group)

                # Test cached objects optimization - there should be no extra DB queries.
                ad_group = ad_group.settings.ad_group
                # Test that initial object is the same as the cached one.
                self.assertEqual(initial_id, id(ad_group))
