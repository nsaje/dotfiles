import json

from django.contrib.auth.models import Permission
from django.test import Client
from django.test import TestCase
from django.urls import reverse

import dash.models
import zemauth.models
from dash import constants
from dash.features.scheduled_reports import models
from utils.magic_mixer import magic_mixer


class ScheduledReportsTestCase(TestCase):
    def setUp(self):
        self.user = magic_mixer.blend(zemauth.models.User, is_active=True)
        self.user.set_password("secret")
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.email, password="secret")

    def test_delete(self):
        report = magic_mixer.blend(
            models.ScheduledReport, state=constants.ScheduledReportState.ACTIVE, user=self.user, query={}
        )

        response = self.client.delete(reverse("scheduled_reports_delete", kwargs={"scheduled_report_id": report.id}))

        report.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(constants.ScheduledReportState.REMOVED, report.state)

    def test_delete_not_logged_in(self):
        self.client.logout()
        report = magic_mixer.blend(
            models.ScheduledReport, state=constants.ScheduledReportState.ACTIVE, user=self.user, query={}
        )

        response = self.client.delete(reverse("scheduled_reports_delete", kwargs={"scheduled_report_id": report.id}))

        report.refresh_from_db()
        self.assertEqual(302, response.status_code)
        self.assertEqual(constants.ScheduledReportState.ACTIVE, report.state)

    def test_delete_not_owner(self):
        report = magic_mixer.blend(models.ScheduledReport, state=constants.ScheduledReportState.ACTIVE, query={})

        response = self.client.delete(reverse("scheduled_reports_delete", kwargs={"scheduled_report_id": report.id}))

        report.refresh_from_db()
        self.assertEqual(403, response.status_code)
        self.assertEqual(constants.ScheduledReportState.ACTIVE, report.state)

    def test_put(self):
        permission = Permission.objects.get(codename="all_accounts_accounts_view")
        self.user.user_permissions.add(permission)

        query = {
            "fields": [{"field": "Content Ad"}],
            "filters": [{"field": "Date", "operator": "between", "from": "2017-04-07", "to": "2017-04-08"}],
            "options": {
                "include_items_with_no_spend": False,
                "all_accounts_in_local_currency": False,
                "include_totals": False,
                "show_archived": False,
                "show_blacklisted_publishers": "all",
                "show_status_date": False,
                "recipients": ["test@test.com"],
            },
        }

        response = self.client.put(
            reverse("scheduled_reports"),
            data=json.dumps(
                {
                    "name": "test report",
                    "query": query,
                    "time_period": "YESTERDAY",
                    "frequency": "DAILY",
                    "day_of_week": "MONDAY",
                }
            ),
        )
        self.assertEqual(200, response.status_code)

        report = models.ScheduledReport.objects.last()
        self.assertEqual(1, report.time_period)
        self.assertEqual(1, report.sending_frequency)
        self.assertEqual(1, report.day_of_week)
        self.assertEqual(query, report.query)
        self.assertEqual(self.user, report.user)

    def test_get(self):
        magic_mixer.cycle(3).blend(
            models.ScheduledReport,
            state=(v for v in constants.ScheduledReportState._VALUES),
            user=self.user,
            query={"filters": [], "fields": [{"field": "Content Ad"}], "options": {"recipients": []}},
        )

        response = self.client.get(reverse("scheduled_reports"))

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json()["data"]["reports"]))

    def test_get_all_for_account(self):
        self._setup_multiple_users_and_accounts()
        response = self.client.get(reverse("scheduled_reports") + "?account_id={}".format(self.account.id))

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json()["data"]["reports"]))

    def test_get_only_users_for_all_accounts(self):
        self._setup_multiple_users_and_accounts()
        response = self.client.get(reverse("scheduled_reports"))

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["data"]["reports"]))

    def _setup_multiple_users_and_accounts(self):
        self.account = magic_mixer.blend(dash.models.Account)
        self.user_1 = magic_mixer.blend(zemauth.models.User, is_active=True)
        self.user_2 = magic_mixer.blend(zemauth.models.User, is_active=True)
        self.account.users.add(self.user)
        self.account.users.add(self.user_1)
        self.account_2 = magic_mixer.blend(dash.models.Account, request=None)
        self.account_2.users.add(self.user_2)
        magic_mixer.cycle(3).blend(
            models.ScheduledReport,
            state=constants.ScheduledReportState.ACTIVE,
            user=(user for user in (self.user, self.user_1, self.user_2)),
            account=(account for account in (self.account, self.account, self.account_2)),
            query={"filters": [], "fields": [{"field": "Content Ad"}], "options": {"recipients": []}},
        )
