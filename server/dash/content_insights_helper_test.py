import datetime

from django import test
from mock import patch

import dash.models
from dash import content_insights_helper
from zemauth.models import User


class ContentInsightsHelperTestCase(test.TestCase):
    fixtures = ["test_views.yaml"]

    def user(self):
        return User.objects.get(pk=2)

    @patch("redshiftapi.api_breakdowns.query")
    def test_fetch_campaign_content_ad_metrics(self, mock_query):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ids = []
        for i in range(3):
            cad = dash.models.ContentAd(
                ad_group=campaign.adgroup_set.first(),
                title="Test Ad {}".format(i),
                url="http://www.zemanta.com",
                batch_id=1,
                archived=False,
            )
            cad.save()
            ids.append(cad.id)

        mock_query.return_value = [
            {"content_ad_id": ids[0], "clicks": 100, "impressions": 100000},
            {"content_ad_id": ids[1], "clicks": 1000, "impressions": 100000},
            {"content_ad_id": ids[2], "clicks": 10000, "impressions": 100000},
        ]

        s, e = datetime.datetime.utcnow(), datetime.datetime.utcnow()
        best, worst = content_insights_helper.fetch_campaign_content_ad_metrics(self.user(), campaign, s, e)
        self.assertCountEqual(
            [
                {"metric": "10.00%", "summary": "Test Ad 2"},
                {"metric": "1.00%", "summary": "Test Ad 1"},
                {"metric": "0.10%", "summary": "Test Ad 0"},
            ],
            best,
        )

    @patch("redshiftapi.api_breakdowns.query")
    def test_fetch_campaign_content_ad_metrics_with_filters(self, mock_query):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ids = []
        for i in range(3):
            cad = dash.models.ContentAd(
                ad_group=campaign.adgroup_set.first(),
                title="Test Ad {}".format(i),
                url="http://www.zemanta.com",
                batch_id=1,
                archived=False,
            )
            cad.save()
            ids.append(cad.id)

        mock_query.return_value = [
            {"content_ad_id": ids[0], "clicks": 10, "impressions": 100},  # ctr 10% but too little impressions
            {"content_ad_id": ids[1], "clicks": 100, "impressions": 10000},  # ctr 1%
            {"content_ad_id": ids[2], "clicks": 1000, "impressions": 10000},  # ctr 10%
        ]

        s, e = datetime.datetime.utcnow(), datetime.datetime.utcnow()
        best, worst = content_insights_helper.fetch_campaign_content_ad_metrics(self.user(), campaign, s, e)
        self.assertCountEqual(
            [{"metric": "10.00%", "summary": "Test Ad 2"}, {"metric": "1.00%", "summary": "Test Ad 1"}], best
        )

    def test_extract_ctr_metric(self):
        title = "Test"
        caids = [1, 2, 3]
        mapped_stats = {
            1: {"clicks": 1000, "impressions": 20000},
            2: {"clicks": 1500, "impressions": 30000},
            3: {"clicks": 2500, "impressions": 50000},
        }
        res = content_insights_helper._extract_ctr_metric(title, caids, mapped_stats)
        self.assertDictEqual({"summary": "Test", "metric": "5.00%", "value": 0.05, "clicks": 5000}, res)

    def test_deduplicate_content_ad_titles(self):
        campaign = dash.models.Campaign.objects.get(pk=1)
        ids = set()
        for i in range(10):
            cad = dash.models.ContentAd(
                ad_group=campaign.adgroup_set.first(),
                title="Test Ad",
                url="http://www.zemanta.com",
                batch_id=1,
                archived=False,
            )
            cad.save()
            ids.add(cad.id)
        res = content_insights_helper._deduplicate_content_ad_titles(campaign=campaign)
        self.assertEqual(["Test Ad"], list(res.keys()))
        self.assertEqual(ids, set(res["Test Ad"]))

        res = content_insights_helper._deduplicate_content_ad_titles(ad_group=campaign.adgroup_set.first())
        self.assertEqual(["Test Ad"], list(res.keys()))
        self.assertEqual(ids, set(res["Test Ad"]))

        for i in range(10):
            cad = dash.models.ContentAd(
                ad_group=campaign.adgroup_set.first(),
                title="Test Ad",
                url="http://www.zemanta.com",
                batch_id=1,
                archived=True,
            )
            cad.save()

        res = content_insights_helper._deduplicate_content_ad_titles(campaign=campaign)
        # archived are ignored
        self.assertEqual(["Test Ad"], list(res.keys()))
        self.assertEqual(ids, set(res["Test Ad"]))

        res = content_insights_helper._deduplicate_content_ad_titles(ad_group=campaign.adgroup_set.first())
        self.assertEqual(["Test Ad"], list(res.keys()))
        self.assertEqual(ids, set(res["Test Ad"]))
