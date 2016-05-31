from django import test
from dash import content_insights_helper
import dash.models


class ContentInsightsHelperTestCase(test.TestCase):
    fixtures = ['test_views.yaml']

    def user(self):
        return User.objects.get(pk=2)

    #def fetch_campaign_content_ad_metrics(user, campaign, start_date, end_date):

    #def _extract_ends(deduplicated_ads, stats):

    def test_extract_ctr_metric(self):
        # title, caids, mapped_stats):
        title = 'Test'
        caids = [1, 2, 3]
        mapped_stats = {
            1: {
                'clicks': 10,
                'impressions': 200,
            },
            2: {
                'clicks': 15,
                'impressions': 300,
            },
            3: {
                'clicks': 25,
                'impressions': 500,
            },
        }
        res = content_insights_helper._extract_ctr_metric(title, caids, mapped_stats)
        self.assertDictEqual({
            'summary': 'Test',
            'metric': '5.00%',
            'value': 0.05,
            'clicks': 50,
        }, res)


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


        res = content_insights_helper._deduplicate_content_ad_titles(
            ad_group=campaign.adgroup_set.first()
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

        res = content_insights_helper._deduplicate_content_ad_titles(
            campaign=campaign
        )
        # archived are ignored
        self.assertEqual(['Test Ad'], res.keys())
        self.assertEqual(ids, set(res['Test Ad']))

        res = content_insights_helper._deduplicate_content_ad_titles(
            ad_group=campaign.adgroup_set.first()
        )
        self.assertEqual(['Test Ad'], res.keys())
        self.assertEqual(ids, set(res['Test Ad']))
