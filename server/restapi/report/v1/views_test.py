import datetime
import json

import mock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

import dash.constants
import dash.models
from dash.features.reports import constants
from dash.features.reports import reports
from utils import threads
from zemauth.models import User


class ReportViewsTest(TestCase):
    fixtures = ["test_api_breakdowns.yaml"]

    def setUp(self):
        self.user = User.objects.get(pk=2)

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @mock.patch("utils.threads.AsyncFunction", threads.MockAsyncFunction)
    @mock.patch("dash.features.reports.reports.ReportJobExecutor", reports.MockJobExecutor)
    def test_new_job(self):
        query = {
            "fields": [{"field": "Content Ad Id"}],
            "filters": [
                {"field": "Ad Group Id", "operator": "=", "value": "1"},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
            ],
        }
        r = self.client.post(reverse("restapi.report.v1:reports_list"), query, format="json")
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "IN_PROGRESS")
        self.assertIn("id", resp_json["data"])

        job_id = int(resp_json["data"]["id"])
        job = dash.models.ReportJob.objects.get(pk=job_id)
        job.status = constants.ReportJobStatus.DONE
        job.save()

        r = self.client.get(reverse("restapi.report.v1:reports_details", kwargs={"job_id": job_id}))
        self.assertEqual(r.status_code, 200)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)
        self.assertEqual(resp_json["data"]["status"], "DONE")
        self.assertEqual(job_id, int(resp_json["data"]["id"]))

    def test_get_report_job_authorization(self):
        query = {
            "fields": [{"field": "Content Ad Id"}],
            "filters": [
                {"field": "Ad Group Id", "operator": "=", "value": "1"},
                {"field": "Date", "operator": "=", "value": "2016-10-10"},
            ],
        }
        r = self.client.post(reverse("restapi.report.v1:reports_list"), query, format="json")
        self.assertEqual(r.status_code, 201)
        resp_json = json.loads(r.content)
        self.assertIsInstance(resp_json["data"], dict)

        job_id = int(resp_json["data"]["id"])

        r = self.client.get(reverse("restapi.report.v1:reports_details", kwargs={"job_id": job_id}))
        self.assertEqual(r.status_code, 200)

        # try as different user
        self.client.force_authenticate(user=User.objects.get(pk=3))
        r = self.client.get(reverse("restapi.report.v1:reports_details", kwargs={"job_id": job_id}))
        self.assertEqual(r.status_code, 403)


class ReportsHeelpersTest(TestCase):
    @mock.patch("utils.dates_helper.local_today")
    def test_date_column_names(self, mock_today):
        mock_today.return_value = datetime.date(2016, 10, 12)
        self.assertEqual(
            reports.ReportJobExecutor._date_column_names(["Status", "Publisher", "Clicks"]),
            (
                ["Status (2016-10-12)", "Publisher", "Clicks"],
                {"Status": "Status (2016-10-12)", "Publisher": "Publisher", "Clicks": "Clicks"},
            ),
        )
