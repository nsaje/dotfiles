import json


from django import test

from reports import views
from zemauth.models import User

class GaContentAdReportTest(test.TestCase):
    fixtures = ['test_reports_base.yaml', 'test_article_stats.yaml']

    sample_data = [
        {
            "content_ad_id": 1000,
            "ga_report": {
                "% New Sessions": "96.02%",
                "Avg. Session Duration": "00:00:12",
                "Bounce Rate": "92.41%",
                "Device Category": "mobile",
                "Landing Page": "/lasko?_z1_caid=1000&_z1_msid=lasko",
                "New Users": "531",
                "Pages / Session": "1.12",
                "Sessions": "553",
                "Yell Free Listings (Goal 1 Completions)": "0",
                "Yell Free Listings (Goal 1 Conversion Rate)": "0.00%",
                "Yell Free Listings (Goal 1 Value)": "\u00a30.00",
                "null": [
                    "",
                    "3,215",
                    "95.43%",
                    "3,068",
                    "88.99%",
                    "1.18",
                    "00:00:17",
                    "0.00%",
                    "0",
                    "\u00a30.00"
                ]
            },
            "goals": {
                "Goal 1": {
                    "conversion_rate": "0.00%",
                    "conversions": "0",
                    "value": "\u00a30.00"
                }
            },
            "report_date": "2015-04-16T00:00:00",
            "source_param": "lasko"
        }
    ]

    def setUp(self):
        self.rf = test.RequestFactory()

    def test_post(self):
        request = self.rf.post('reports/ga/contentadstats', data=json.dumps(GaContentAdReportTest.sample_data), content_type='application/json')
        request.user = User.objects.get(pk=1)
        content_ad_report = views.GaContentAdReport()
        response = content_ad_report.post(request)
        self.assertEqual(response.status_code, 200)
