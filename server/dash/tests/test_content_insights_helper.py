from django import test
from dash import content_insights_helper
import dash.models


class ContentInsightsHelperTestCase(test.TestCase):
    fixtures = ['test_views.yaml']

    def user(self):
        return User.objects.get(pk=2)

    #def fetch_campaign_content_ad_metrics(user, campaign, start_date, end_date):

    #def _extract_ends(deduplicated_ads, stats):

    #def _extract_ctr_metric(title, caids, mapped_stats):

    def test_deduplicate_content_ad_titles(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ids = set()
        for i in range(10):
            cad = dash.models.ContentAd.objects.create(
                ad_group=campaign.adgroup_set.first(),
                title='Test Ad',
                url='http://www.zemanta.com',
                batch_id=1,
                archived=False,
            )
            ids.add(cad.id)
        res = content_insights_helper._deduplicate_content_ad_titles(
            campaign=campaign
        )
        self.assertEqual(['Test Ad'], res.keys())
        self.assertEqual(ids, set(res['Test Ad']))

        for i in range(10):
            cad = dash.models.ContentAd.objects.create(
                ad_group=campaign.adgroup_set.first(),
                title='Test Ad',
                url='http://www.zemanta.com',
                batch_id=1,
                archived=True,
            )
            ids.add(cad.id)

        # archived are ignored
        self.assertEqual(['Test Ad'], res.keys())
        self.assertEqual(ids, set(res['Test Ad']))
