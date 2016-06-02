import datetime
from django import test
from dash import content_insights_helper
import dash.models

from zemauth.models import User

from mock import patch


class ContentInsightsHelperTestCase(test.TestCase):
    fixtures = ['test_views.yaml']

    def user(self):
        return User.objects.get(pk=2)

    @patch('dash.stats_helper.get_content_ad_stats_with_conversions')
    def test_fetch_campaign_content_ad_metrics(self, mock_get_stats):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ids = []
        for i in range(3):
            cad = dash.models.ContentAd.objects.create(
                ad_group=campaign.adgroup_set.first(),
                title='Test Ad {}'.format(i),
                url='http://www.zemanta.com',
                batch_id=1,
                archived=False,
            )
            ids.append(cad.id)

        mock_get_stats.return_value = [
            {
                'content_ad': ids[0],
                'clicks': 1,
                'impressions': 1000,
            },
            {
                'content_ad': ids[1],
                'clicks': 10,
                'impressions': 1000,
            },
            {
                'content_ad': ids[2],
                'clicks': 100,
                'impressions': 1000,
            }
        ]

        s, e = datetime.datetime.utcnow(), datetime.datetime.utcnow()
        best, worst = content_insights_helper.fetch_campaign_content_ad_metrics(self.user(), campaign, s, e)
        self.assertItemsEqual([
            {
                'metric': '10.00%',
                'summary': 'Test Ad 2',
            },
            {
                'metric': '1.00%',
                'summary': 'Test Ad 1',
            },
            {
                'metric': '0.10%',
                'summary': 'Test Ad 0',
            }
        ], best)

    def test_extract_ctr_metric(self):
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
