import datetime

import dash.constants
import dash.models
from stats import constraints_helper
from utils import test_helper
from utils.base_test_case import BaseTestCase
from utils.magic_mixer import magic_mixer
from zemauth.features.entity_permission import Permission
from zemauth.models import User


class PrepareConstraintsTestCase(BaseTestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def test_prepare_all_accounts_constraints(self):
        sources = dash.models.Source.objects.all()
        user = User.objects.get(pk=2)
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)

        self.assertDictEqual(
            constraints_helper.prepare_all_accounts_constraints(user, start_date, end_date, sources),
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "allowed_accounts": test_helper.QuerySetMatcher(dash.models.Account.objects.all()),
                "allowed_campaigns": test_helper.QuerySetMatcher(dash.models.Campaign.objects.filter(pk__in=[1])),
                "publisher_blacklist": test_helper.QuerySetMatcher([]),
                "publisher_whitelist": test_helper.QuerySetMatcher([]),
                "publisher_group_targeting": {
                    "account": {"excluded": set(), "included": set()},
                    "campaign": {"excluded": set(), "included": set()},
                    "ad_group": {"excluded": set(), "included": set()},
                    "global": {"excluded": set()},
                },
                "publisher_blacklist_filter": "all",
            },
        )

        self.assertDictEqual(
            constraints_helper.prepare_all_accounts_constraints(user, start_date, end_date, sources),
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "allowed_accounts": test_helper.QuerySetMatcher(dash.models.Account.objects.all()),
                "allowed_campaigns": test_helper.QuerySetMatcher(dash.models.Campaign.objects.filter(pk__in=[1])),
                "publisher_blacklist": test_helper.QuerySetMatcher([]),
                "publisher_whitelist": test_helper.QuerySetMatcher(dash.models.PublisherGroupEntry.objects.none()),
                "publisher_group_targeting": {
                    "account": {"excluded": set(), "included": set()},
                    "campaign": {"excluded": set(), "included": set()},
                    "ad_group": {"excluded": set(), "included": set()},
                    "global": {"excluded": set()},
                },
                "publisher_blacklist_filter": "all",
            },
        )

        self.assertDictEqual(
            constraints_helper.prepare_all_accounts_constraints(user, start_date, end_date, sources),
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "allowed_accounts": test_helper.QuerySetMatcher(dash.models.Account.objects.all()),
                "allowed_campaigns": test_helper.QuerySetMatcher(dash.models.Campaign.objects.filter(pk__in=[1])),
                "publisher_blacklist": test_helper.QuerySetMatcher([]),
                "publisher_whitelist": test_helper.QuerySetMatcher(dash.models.PublisherGroupEntry.objects.none()),
                "publisher_group_targeting": {
                    "account": {"excluded": set(), "included": set()},
                    "campaign": {"excluded": set(), "included": set()},
                    "ad_group": {"excluded": set(), "included": set()},
                    "global": {"excluded": set()},
                },
                "publisher_blacklist_filter": "all",
            },
        )

    def test_prepare_account_constraints(self):
        sources = dash.models.Source.objects.all()
        user = User.objects.get(pk=2)
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)
        account = dash.models.Account.objects.get(pk=1)

        self.assertDictEqual(
            constraints_helper.prepare_account_constraints(user, account, start_date, end_date, sources),
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "account": account,
                "allowed_campaigns": test_helper.QuerySetMatcher(dash.models.Campaign.objects.filter(pk__in=[1])),
                "allowed_ad_groups": test_helper.QuerySetMatcher(dash.models.AdGroup.objects.filter(pk__in=[1, 2])),
                "publisher_blacklist": test_helper.QuerySetMatcher(
                    dash.models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[5])
                ),
                "publisher_whitelist": test_helper.QuerySetMatcher(dash.models.PublisherGroupEntry.objects.none()),
                "publisher_group_targeting": {
                    "account": {"excluded": set([5]), "included": set()},
                    "campaign": {"excluded": set(), "included": set()},
                    "ad_group": {"excluded": set(), "included": set()},
                    "global": {"excluded": set()},
                },
                "publisher_blacklist_filter": "all",
            },
        )

    def test_prepare_campaign_constraints(self):
        sources = dash.models.Source.objects.all()
        user = User.objects.get(pk=2)
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)
        campaign = dash.models.Campaign.objects.get(pk=1)

        self.assertDictEqual(
            constraints_helper.prepare_campaign_constraints(user, campaign, start_date, end_date, sources),
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "account": dash.models.Account.objects.get(pk=1),
                "campaign": dash.models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": test_helper.QuerySetMatcher(dash.models.AdGroup.objects.filter(campaign_id=1)),
                "allowed_content_ads": test_helper.QuerySetMatcher(
                    dash.models.ContentAd.objects.filter(ad_group__campaign_id=1).exclude_archived()
                ),
                "publisher_blacklist": test_helper.QuerySetMatcher(
                    dash.models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[5])
                ),
                "publisher_whitelist": test_helper.QuerySetMatcher(
                    dash.models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[4])
                ),
                "publisher_group_targeting": {
                    "account": {"excluded": set([5]), "included": set()},
                    "campaign": {"excluded": set(), "included": set([4])},
                    "ad_group": {"excluded": set(), "included": set()},
                    "global": {"excluded": set()},
                },
                "publisher_blacklist_filter": "all",
            },
        )

        self.assertDictEqual(
            constraints_helper.prepare_campaign_constraints(user, campaign, start_date, end_date, sources),
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "account": dash.models.Account.objects.get(pk=1),
                "campaign": dash.models.Campaign.objects.get(pk=1),
                "allowed_ad_groups": test_helper.QuerySetMatcher(dash.models.AdGroup.objects.filter(campaign_id=1)),
                "allowed_content_ads": test_helper.QuerySetMatcher(
                    dash.models.ContentAd.objects.filter(ad_group__campaign_id=1).exclude_archived()
                ),
                "publisher_blacklist": test_helper.QuerySetMatcher(
                    dash.models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[5])
                ),
                "publisher_whitelist": test_helper.QuerySetMatcher(
                    dash.models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[4])
                ),
                "publisher_group_targeting": {
                    "account": {"excluded": set([5]), "included": set()},
                    "campaign": {"excluded": set(), "included": set([4])},
                    "ad_group": {"excluded": set(), "included": set()},
                    "global": {"excluded": set()},
                },
                "publisher_blacklist_filter": "all",
            },
        )

    def test_prepare_ad_group_constraints(self):
        sources = dash.models.Source.objects.all()
        user = User.objects.get(pk=2)
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)

        self.assertDictEqual(
            constraints_helper.prepare_ad_group_constraints(user, ad_group, start_date, end_date, sources),
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "account": dash.models.Account.objects.get(pk=1),
                "campaign": dash.models.Campaign.objects.get(pk=1),
                "ad_group": dash.models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": test_helper.QuerySetMatcher(
                    dash.models.ContentAd.objects.filter(ad_group_id=1).exclude_archived()
                ),
                "publisher_blacklist_filter": dash.constants.PublisherBlacklistFilter.SHOW_ALL,
                "publisher_blacklist": test_helper.QuerySetMatcher(
                    dash.models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[3, 5])
                ),
                "publisher_whitelist": test_helper.QuerySetMatcher(
                    dash.models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[2, 4])
                ),
                "publisher_group_targeting": {
                    "ad_group": {"included": set([2]), "excluded": set([3])},
                    "campaign": {"included": set([4]), "excluded": set()},
                    "account": {"included": set(), "excluded": set([5])},
                    "global": {"excluded": set()},
                },
            },
        )

    def test_prepare_ad_group_constraints_publishers(self):
        sources = dash.models.Source.objects.all()
        user = User.objects.get(pk=2)
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)
        ad_group = dash.models.AdGroup.objects.get(pk=1)

        self.assertDictEqual(
            constraints_helper.prepare_ad_group_constraints(
                user,
                ad_group,
                start_date,
                end_date,
                sources,
                show_blacklisted_publishers=dash.constants.PublisherBlacklistFilter.SHOW_ACTIVE,
            ),
            {
                "date__gte": start_date,
                "date__lte": end_date,
                "show_archived": False,
                "filtered_sources": test_helper.QuerySetMatcher(sources),
                "account": dash.models.Account.objects.get(pk=1),
                "campaign": dash.models.Campaign.objects.get(pk=1),
                "ad_group": dash.models.AdGroup.objects.get(pk=1),
                "allowed_content_ads": test_helper.QuerySetMatcher(
                    dash.models.ContentAd.objects.filter(ad_group_id=1).exclude_archived()
                ),
                "publisher_blacklist_filter": dash.constants.PublisherBlacklistFilter.SHOW_ACTIVE,
                "publisher_blacklist": test_helper.QuerySetMatcher(
                    dash.models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[3, 5])
                ),
                "publisher_whitelist": test_helper.QuerySetMatcher(
                    dash.models.PublisherGroupEntry.objects.filter(publisher_group_id__in=[2, 4])
                ),
                "publisher_group_targeting": {
                    "ad_group": {"included": set([2]), "excluded": set([3])},
                    "campaign": {"included": set([4]), "excluded": set()},
                    "account": {"included": set(), "excluded": set([5])},
                    "global": {"excluded": set()},
                },
            },
        )


class NarrowFilteredSourcesTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.account = self.mix_account(self.user, permissions=[Permission.READ])

        self.source_credentials = magic_mixer.cycle(2).blend(dash.models.SourceCredentials)
        self.sources = dash.models.Source.objects.all()

        self.ad_group = magic_mixer.blend(dash.models.AdGroup, campaign__account=self.account)
        self.ad_group_sources = magic_mixer.cycle(2).blend(
            dash.models.AdGroupSource,
            ad_group=self.ad_group,
            source=(sc.source for sc in self.source_credentials),
            source_credentials=(sc for sc in self.source_credentials),
        )

        self.start_date = datetime.date(2018, 5, 1)
        self.end_date = datetime.date(2018, 6, 1)

    def test_prepare_all_accounts_constraints(self):
        constraints = constraints_helper.prepare_all_accounts_constraints(
            self.user, self.start_date, self.end_date, dash.models.Source.objects.all(), only_used_sources=True
        )
        self.assertEqual(constraints["filtered_sources"], test_helper.QuerySetMatcher(dash.models.Source.objects.all()))

        dash.models.AdGroupSource.objects.filter(source=self.sources[1]).update(ad_review_only=True)
        constraints = constraints_helper.prepare_all_accounts_constraints(
            self.user, self.start_date, self.end_date, dash.models.Source.objects.all(), only_used_sources=True
        )
        self.assertEqual(constraints["filtered_sources"], test_helper.QuerySetMatcher([self.sources[0]]))

    def test_prepare_account_constraints(self):
        constraints = constraints_helper.prepare_account_constraints(
            self.user,
            self.ad_group.campaign.account,
            self.start_date,
            self.end_date,
            dash.models.Source.objects.all(),
            only_used_sources=True,
        )
        self.assertEqual(constraints["filtered_sources"], test_helper.QuerySetMatcher(dash.models.Source.objects.all()))

        dash.models.AdGroupSource.objects.filter(source=self.sources[1]).update(ad_review_only=True)
        constraints = constraints_helper.prepare_account_constraints(
            self.user,
            self.ad_group.campaign.account,
            self.start_date,
            self.end_date,
            dash.models.Source.objects.all(),
            only_used_sources=True,
        )
        self.assertEqual(constraints["filtered_sources"], test_helper.QuerySetMatcher([self.sources[0]]))

    def test_prepare_campaign_constraints(self):
        constraints = constraints_helper.prepare_campaign_constraints(
            self.user,
            self.ad_group.campaign,
            self.start_date,
            self.end_date,
            dash.models.Source.objects.all(),
            only_used_sources=True,
        )
        self.assertEqual(constraints["filtered_sources"], test_helper.QuerySetMatcher(dash.models.Source.objects.all()))

        dash.models.AdGroupSource.objects.filter(source=self.sources[1]).update(ad_review_only=True)
        constraints = constraints_helper.prepare_campaign_constraints(
            self.user,
            self.ad_group.campaign,
            self.start_date,
            self.end_date,
            dash.models.Source.objects.all(),
            only_used_sources=True,
        )
        self.assertEqual(constraints["filtered_sources"], test_helper.QuerySetMatcher([self.sources[0]]))

    def test_prepare_ad_group_constraints(self):
        constraints = constraints_helper.prepare_ad_group_constraints(
            self.user,
            self.ad_group,
            self.start_date,
            self.end_date,
            dash.models.Source.objects.all(),
            only_used_sources=True,
        )
        self.assertEqual(constraints["filtered_sources"], test_helper.QuerySetMatcher(dash.models.Source.objects.all()))

        dash.models.AdGroupSource.objects.filter(source=self.sources[1]).update(ad_review_only=True)
        constraints = constraints_helper.prepare_ad_group_constraints(
            self.user,
            self.ad_group,
            self.start_date,
            self.end_date,
            dash.models.Source.objects.all(),
            only_used_sources=True,
        )
        self.assertEqual(constraints["filtered_sources"], test_helper.QuerySetMatcher([self.sources[0]]))
