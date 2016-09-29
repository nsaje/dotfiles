import datetime

from django.test import TestCase

from utils import test_helper
from zemauth.models import User

from dash import models

from stats import constraints_helper


class PrepareConstraints(TestCase):
    fixtures = ['test_api_breakdowns.yaml']

    def test_prepare_all_accounts_constraints(self):
        sources = models.Source.objects.all()
        user = User.objects.get(pk=1)
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)

        self.assertDictEqual(
            constraints_helper.prepare_all_accounts_constraints(user, ['account_id'], start_date, end_date, sources),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'allowed_accounts': test_helper.QuerySetMatcher(models.Account.objects.all()),
                'allowed_campaigns': test_helper.QuerySetMatcher(models.Campaign.objects.filter(pk__in=[1])),
            }
        )

        self.assertDictEqual(
            constraints_helper.prepare_all_accounts_constraints(
                user, ['account_id', 'campaign_id'], start_date, end_date, sources
            ),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'allowed_accounts': test_helper.QuerySetMatcher(models.Account.objects.all()),
                'allowed_campaigns': test_helper.QuerySetMatcher(models.Campaign.objects.filter(pk__in=[1])),
            }
        )

        self.assertDictEqual(
            constraints_helper.prepare_all_accounts_constraints(user, ['source_id'], start_date, end_date, sources),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'allowed_accounts': test_helper.QuerySetMatcher(models.Account.objects.all()),
                'allowed_campaigns': test_helper.QuerySetMatcher(
                    models.Campaign.objects.filter(pk__in=[1, 2])),  # show archived
            }
        )

    def test_prepare_account_constraints(self):
        sources = models.Source.objects.all()
        user = User.objects.get(pk=1)
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)
        account = models.Account.objects.get(pk=1)

        self.assertDictEqual(
            constraints_helper.prepare_account_constraints(user, account, ['source_id', 'campaign_id'],
                                                           start_date, end_date, sources),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'account': account,
                'allowed_campaigns': test_helper.QuerySetMatcher(models.Campaign.objects.filter(pk__in=[1, 2])),
                'allowed_ad_groups': test_helper.QuerySetMatcher(models.AdGroup.objects.filter(campaign_id__in=[1, 2])),
            }
        )

    def test_prepare_campaign_constraints(self):
        sources = models.Source.objects.all()
        user = User.objects.get(pk=1)
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)
        campaign = models.Campaign.objects.get(pk=1)

        self.assertDictEqual(
            constraints_helper.prepare_campaign_constraints(user, campaign, ['campaign_id', 'ad_group_id'],
                                                            start_date, end_date, sources),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'account': models.Account.objects.get(pk=1),
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': test_helper.QuerySetMatcher(models.AdGroup.objects.filter(campaign_id=1)),
                'allowed_content_ads': test_helper.QuerySetMatcher(
                    models.ContentAd.objects.filter(ad_group__campaign_id=1).exclude_archived()),
            }
        )

        self.assertDictEqual(
            constraints_helper.prepare_campaign_constraints(user, campaign, ['campaign_id', 'content_ad_id'],
                                                            start_date, end_date, sources),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'account': models.Account.objects.get(pk=1),
                'campaign': models.Campaign.objects.get(pk=1),
                'allowed_ad_groups': test_helper.QuerySetMatcher(models.AdGroup.objects.filter(campaign_id=1)),
                'allowed_content_ads': test_helper.QuerySetMatcher(
                    models.ContentAd.objects.filter(ad_group__campaign_id=1).exclude_archived()),
            }
        )

    def test_prepare_ad_group_constraints(self):
        sources = models.Source.objects.all()
        user = User.objects.get(pk=1)
        start_date = datetime.date(2016, 1, 1)
        end_date = datetime.date(2016, 2, 1)
        ad_group = models.AdGroup.objects.get(pk=1)

        self.assertDictEqual(
            constraints_helper.prepare_ad_group_constraints(user, ad_group, ['ad_group_id', 'content_ad_id'],
                                                            start_date, end_date, sources),
            {
                'date__gte': start_date,
                'date__lte': end_date,
                'show_archived': False,
                'filtered_sources': test_helper.QuerySetMatcher(sources),
                'account': models.Account.objects.get(pk=1),
                'campaign': models.Campaign.objects.get(pk=1),
                'ad_group': models.AdGroup.objects.get(pk=1),
                'allowed_content_ads': test_helper.QuerySetMatcher(
                    models.ContentAd.objects.filter(ad_group_id=1).exclude_archived()),
            }
        )
