import json
from datetime import date

from django.test import TestCase
from django.test.utils import override_settings
from django.urls import reverse
from mock import patch


@patch("dash.features.supply_reports.service.get_crossvalidation_stats")
@patch("utils.request_signer.verify_wsgi_request")
@override_settings(BIDDER_API_SIGN_KEY="test_api_key")
class CrossvalidationViewTest(TestCase):
    fixtures = ["test_api_views"]

    def test_no_parameters(self, mock_verify_wsgi_request, mock_query):
        response = self.client.get(reverse("api.crossvalidation"))

        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, "test_api_key")
        self.assertEqual(response.status_code, 400)

    def test_valid_request(self, mock_verify_wsgi_request, mock_cv):
        mock_cv.return_value = [("test1", 10, 2, 0.033), ("test2", 5, 0, 0.0)]

        response = self.client.get(
            reverse("api.crossvalidation"), data={"start_date": "2015-11-05", "end_date": "2015-11-05"}
        )

        mock_verify_wsgi_request.assert_called_with(response.wsgi_request, "test_api_key")

        mock_cv.assert_called_once_with(date(2015, 11, 5), date(2015, 11, 5))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content),
            {
                "status": "OK",
                "data": [
                    {"cost": 0.033, "impressions": 10, "clicks": 2, "bidder_slug": "test1"},
                    {"cost": 0.0, "impressions": 5, "clicks": 0, "bidder_slug": "test2"},
                ],
            },
        )
