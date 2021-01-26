import datetime

import core.features.publisher_groups
import core.models
from utils import test_helper
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission

from . import constraints_helper


class ReportsConstraintsTestCase(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        magic_mixer.blend_source_w_defaults(), magic_mixer.blend_source_w_defaults()

    def test_filter_by_user(self):
        sources = core.models.Source.objects.all()
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        content_ad = magic_mixer.blend(core.models.ContentAd, ad_group__campaign__account=account)
        magic_mixer.blend(core.models.ContentAd)  # someone else's content ad

        self.assertDictEqual(
            constraints_helper.prepare_constraints(
                self.user, ["content_ad_id"], start_date, end_date, sources, show_archived=False
            ),
            {
                "ad_group": None,
                "allowed_accounts": test_helper.QuerySetMatcher([content_ad.ad_group.campaign.account]),
                "allowed_campaigns": test_helper.QuerySetMatcher([content_ad.ad_group.campaign]),
                "allowed_ad_groups": test_helper.QuerySetMatcher([content_ad.ad_group]),
                "allowed_content_ads": test_helper.QuerySetMatcher([content_ad]),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 1),
                "filtered_sources": sources,
                "publisher_blacklist": None,
                "publisher_blacklist_filter": None,
                "publisher_group_targeting": None,
                "publisher_whitelist": None,
                "show_archived": False,
            },
        )

    def test_show_archived(self):
        sources = core.models.Source.objects.all()
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)

        account_1 = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        account_2 = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        accounts = [account_1, account_2]

        campaigns = magic_mixer.cycle(2).blend(core.models.Campaign, account=accounts[1])
        ad_groups = magic_mixer.cycle(2).blend(core.models.AdGroup, campaign=campaigns[1])
        content_ads = magic_mixer.cycle(2).blend(core.models.ContentAd, ad_group=ad_groups[1])
        content_ads[0].archived = True
        content_ads[0].save()
        ad_groups[0].settings.update(None, archived=True)
        campaigns[0].settings.update(None, archived=True)
        accounts[0].settings.update(None, archived=True)

        self.assertDictEqual(
            constraints_helper.prepare_constraints(
                self.user, ["content_ad_id"], start_date, end_date, sources, show_archived=False
            ),
            {
                "ad_group": None,
                "allowed_accounts": test_helper.QuerySetMatcher([accounts[1]]),
                "allowed_campaigns": test_helper.QuerySetMatcher([campaigns[1]]),
                "allowed_ad_groups": test_helper.QuerySetMatcher([ad_groups[1]]),
                "allowed_content_ads": test_helper.QuerySetMatcher([content_ads[1]]),
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 1),
                "filtered_sources": sources,
                "publisher_blacklist": None,
                "publisher_blacklist_filter": None,
                "publisher_group_targeting": None,
                "publisher_whitelist": None,
                "show_archived": False,
            },
        )

    def test_archived_ad_group_explicit(self):
        sources = core.models.Source.objects.all()
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)
        account = self.mix_account(self.user, permissions=[Permission.READ, Permission.WRITE])
        ad_group = magic_mixer.blend(core.models.AdGroup, campaign__account=account)
        ad_group.settings.update(None, archived=True)

        self.assertDictEqual(
            constraints_helper.prepare_constraints(
                self.user,
                ["ad_group_id"],
                start_date,
                end_date,
                sources,
                show_archived=False,
                ad_group_ids=[ad_group.id],
            ),
            {
                "ad_group": ad_group,
                "allowed_accounts": test_helper.QuerySetMatcher([ad_group.campaign.account]),
                "allowed_campaigns": test_helper.QuerySetMatcher([ad_group.campaign]),
                "allowed_ad_groups": test_helper.QuerySetMatcher([]),
                "allowed_content_ads": None,
                "date__gte": datetime.date(2016, 1, 1),
                "date__lte": datetime.date(2016, 2, 1),
                "filtered_sources": sources,
                "publisher_blacklist": None,
                "publisher_blacklist_filter": None,
                "publisher_group_targeting": None,
                "publisher_whitelist": None,
                "show_archived": False,
            },
        )
