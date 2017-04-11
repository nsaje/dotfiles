import json

from django.contrib.auth.models import Permission
from django.core.urlresolvers import reverse
from django.test import TestCase, Client
from mixer.backend.django import mixer

from dash import constants
from dash.features.scheduled_reports import models
import zemauth.models


class ScheduledReportsTestCase(TestCase):

    def setUp(self):
        self.user = mixer.blend(zemauth.models.User, is_active=True)
        self.user.set_password('secret')
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.email, password='secret')

    def test_delete(self):
        report = mixer.blend(
            models.ScheduledReport,
            state=constants.ScheduledReportState.ACTIVE,
            user=self.user,
            query={},
        )

        response = self.client.delete(
            reverse('scheduled_reports_delete', kwargs={'scheduled_report_id': report.id}),
        )

        report.refresh_from_db()
        self.assertEqual(200, response.status_code)
        self.assertEqual(constants.ScheduledReportState.REMOVED, report.state)

    def test_delete_not_logged_in(self):
        self.client.logout()
        report = mixer.blend(
            models.ScheduledReport,
            state=constants.ScheduledReportState.ACTIVE,
            user=self.user,
            query={},
        )

        response = self.client.delete(
            reverse('scheduled_reports_delete', kwargs={'scheduled_report_id': report.id}),
        )

        report.refresh_from_db()
        self.assertEqual(302, response.status_code)
        self.assertEqual(constants.ScheduledReportState.ACTIVE, report.state)

    def test_delete_not_owner(self):
        report = mixer.blend(models.ScheduledReport, state=constants.ScheduledReportState.ACTIVE, query={})

        response = self.client.delete(
            reverse('scheduled_reports_delete', kwargs={'scheduled_report_id': report.id}),
        )

        report.refresh_from_db()
        self.assertEqual(403, response.status_code)
        self.assertEqual(constants.ScheduledReportState.ACTIVE, report.state)

    def test_put(self):
        permission = Permission.objects.get(codename='all_accounts_accounts_view')
        self.user.user_permissions.add(permission)

        query = {
            'fields': [{
                'field': 'Content Ad',
            }],
            'filters': [{
                'field': 'Date',
                'operator': 'between',
                'from': '2017-04-07',
                'to': '2017-04-08'
            }],
            'options': {
                'include_items_with_no_spend': False,
                'include_totals': False,
                'show_archived': False,
                'show_blacklisted_publishers': 'all',
                'show_status_date': False,
                'recipients': ['test@test.com'],
            },
        }

        response = self.client.put(
            reverse('scheduled_reports'),
            data=json.dumps({
                'name': 'test report',
                'query': query,
                'time_period': 'YESTERDAY',
                'frequency': 'DAILY',
                'day_of_week': 'MONDAY',
            }),
        )
        self.assertEqual(200, response.status_code)

        report = models.ScheduledReport.objects.last()
        self.assertEqual(1, report.time_period)
        self.assertEqual(1, report.sending_frequency)
        self.assertEqual(1, report.day_of_week)
        self.assertEqual(query, report.query)
        self.assertEqual(self.user, report.user)

    def test_get(self):
        mixer.cycle(3).blend(
            models.ScheduledReport,
            state=(v for v in constants.ScheduledReportState._VALUES),
            user=self.user,
            query={'filters': [], 'fields': [{'field': 'Content Ad'}], 'options': {'recipients': []}},
        )

        response = self.client.get(
            reverse('scheduled_reports'),
        )

        self.assertEqual(200, response.status_code)
        self.assertEqual(2, len(response.json()['data']['reports']))
