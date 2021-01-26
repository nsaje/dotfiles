import datetime
import threading

import django_pglocks
import mock
from django.conf import settings
from django.test import TestCase
from django.test import TransactionTestCase
from django.utils import timezone

from dcron import alerts
from dcron import commands
from dcron import constants
from dcron import exceptions
from dcron import models
from utils import pagerduty_helper


class ExtractManagementCommandNameTestCase(TestCase):
    def test_none(self):
        with self.assertRaises(exceptions.ParameterException):
            commands.extract_management_command_name(None)

    def test_empty(self):
        with self.assertRaises(exceptions.ParameterException):
            commands.extract_management_command_name("")

    def test_single_parameter(self):
        with self.assertRaises(exceptions.ParameterException):
            commands.extract_management_command_name("./manage.py")

    def test_wrong_base_command(self):
        with self.assertRaises(exceptions.ParameterException):
            commands.extract_management_command_name("./manage.py migrate")

    def test_correct_command(self):
        command_name = commands.extract_management_command_name("%s somecommand" % settings.DCRON["base_command"])
        self.assertEqual(command_name, "somecommand")

    def test_correct_command_args(self):
        command_name = commands.extract_management_command_name("%s somecommand 7" % settings.DCRON["base_command"])
        self.assertEqual(command_name, "somecommand")

    def test_correct_command_args_params(self):
        command_name = commands.extract_management_command_name(
            "%s somecommand 7 --test" % settings.DCRON["base_command"]
        )
        self.assertEqual(command_name, "somecommand")


DUMMY_COMMAND = "dummy_command"


class DCronCommandTestCase(TransactionTestCase):
    """
    Test DCronCommand class - verify that an advisory lock is obtained
    and that it creates or updates the corresponding DCronJob record.
    """

    def _assert_history(self, dcron_job, status, expected_max_duration=settings.DCRON["default_max_duration"]):
        dcron_job.refresh_from_db()
        dcron_job_history = models.DCronJobHistory.objects.filter(command_name=dcron_job.command_name).first()
        self.assertEqual(dcron_job_history.status, status)
        self.assertEqual(dcron_job_history.status, dcron_job.alert)
        self.assertEqual(dcron_job_history.host, dcron_job.host)
        self.assertEqual(dcron_job_history.executed_dt, dcron_job.executed_dt)
        self.assertEqual(dcron_job_history.completed_dt, dcron_job.completed_dt)
        self.assertEqual(dcron_job_history.expected_max_duration, expected_max_duration)

    @mock.patch("sys.argv", ["manage.py", DUMMY_COMMAND])
    @mock.patch("utils.metrics_compat.incr")
    @mock.patch("utils.metrics_compat.timing")
    def test_handle(self, mock_influx_timing, mock_influx_incr):

        event_1 = threading.Event()
        event_2 = threading.Event()
        event_3 = threading.Event()

        class DummyCommand(commands.DCronCommand):
            def handle(self, *args, **options):
                super().handle(*args, **options)
                event_3.set()

            def _handle(self, *args, **options):
                event_1.set()
                event_2.wait()

        dummy_command = DummyCommand()

        def run_command():
            dummy_command.execute(**{"no_color": None, "force_color": None, "stdout": None, "stderr": None})

        dcron_job_qs = models.DCronJob.objects.filter(command_name=DUMMY_COMMAND)

        self.assertEqual(dcron_job_qs.count(), 0)

        self.assertFalse(models.DCronJobHistory.objects.filter(command_name=DUMMY_COMMAND).exists())

        command_thread = threading.Thread(target=run_command)

        try:
            command_thread.start()

            event_1.wait()  # Wait until DummyCommand._handle starts running.

            mock_influx_incr.assert_has_calls([mock.call("dcron_command_count", 1, command_name=DUMMY_COMMAND)])

            self.assertEqual(dcron_job_qs.count(), 1)

            dcron_job = dcron_job_qs.get()
            self.assertIsNotNone(dcron_job.executed_dt)
            self.assertIsNone(dcron_job.completed_dt)
            self.assertEqual(dcron_job.host, settings.HOSTNAME)
            self.assertEqual(dcron_job.alert, constants.Alert.OK)

            try:
                with django_pglocks.advisory_lock(DUMMY_COMMAND, wait=False) as acquired:
                    self.assertFalse(acquired)

                self.assertEqual(dcron_job_qs.count(), 1)

                dcron_job = dcron_job_qs.get()
                self.assertIsNotNone(dcron_job.executed_dt)
                self.assertIsNone(dcron_job.completed_dt)
                self.assertEqual(dcron_job.host, settings.HOSTNAME)
                self.assertEqual(dcron_job.alert, constants.Alert.OK)

            finally:
                event_2.set()  # Signal DummyCommand._handle that it can finish.

            event_3.wait()  # Wait until DummyCommand.handle completes.

            call_args_list = mock_influx_timing.call_args_list
            self.assertEqual(len(call_args_list), 1)
            self.assertEqual(call_args_list[0][0][0], "dcron_command_duration")
            self.assertDictEqual(call_args_list[0][1], {"command_name": DUMMY_COMMAND})

            self.assertEqual(dcron_job_qs.count(), 1)

            dcron_job = dcron_job_qs.get()
            self.assertIsNotNone(dcron_job.executed_dt)
            self.assertIsNotNone(dcron_job.completed_dt)
            self.assertTrue(dcron_job.completed_dt > dcron_job.executed_dt)
            self.assertEqual(dcron_job.host, settings.HOSTNAME)
            self.assertEqual(dcron_job.alert, constants.Alert.OK)

            with django_pglocks.advisory_lock(DUMMY_COMMAND, wait=False) as acquired:
                self.assertTrue(acquired)
        finally:
            event_2.set()

        self.assertEqual(models.DCronJobHistory.objects.filter(command_name=DUMMY_COMMAND).count(), 1)
        self._assert_history(dcron_job, constants.Alert.OK)

    @mock.patch("sys.argv", ["manage.py", DUMMY_COMMAND])
    @mock.patch("utils.metrics_compat.incr")
    @mock.patch("utils.metrics_compat.timing")
    @mock.patch("utils.pagerduty_helper._post_event")
    @mock.patch("utils.slack.publish")
    def test_failure(self, mock_slack_publish, mock_post_event, mock_influx_timing, mock_influx_incr):
        class DummyCommand(commands.DCronCommand):
            def _handle(self, *args, **options):
                raise RuntimeError("TEST!")

        self.assertFalse(models.DCronJobHistory.objects.filter(command_name=DUMMY_COMMAND).exists())

        dummy_command = DummyCommand()

        dummy_command.execute(**{"no_color": None, "force_color": None, "stdout": None, "stderr": None})

        dcron_job_qs = models.DCronJob.objects.filter(command_name=DUMMY_COMMAND)

        self.assertEqual(dcron_job_qs.count(), 1)

        dcron_job = dcron_job_qs.get()
        self.assertIsNotNone(dcron_job.executed_dt)
        self.assertIsNotNone(dcron_job.completed_dt)
        self.assertEqual(dcron_job.host, settings.HOSTNAME)
        self.assertEqual(dcron_job.alert, constants.Alert.FAILURE)

        mock_influx_incr.assert_has_calls([mock.call("dcron_command_count", 1, command_name=DUMMY_COMMAND)])

        call_args_list = mock_influx_timing.call_args_list
        self.assertEqual(len(call_args_list), 1)
        self.assertEqual(call_args_list[0][0][0], "dcron_command_duration")
        self.assertDictEqual(call_args_list[0][1], {"command_name": DUMMY_COMMAND})

        mock_post_event.assert_has_calls(
            [
                mock.call(
                    "trigger",
                    pagerduty_helper.PagerDutyEventType.Z1,
                    DUMMY_COMMAND,
                    alerts._alert_message(DUMMY_COMMAND, constants.Alert.FAILURE),
                    event_severity=pagerduty_helper.PagerDutyEventSeverity.WARNING,
                    details=None,
                )
            ]
        )

        mock_slack_publish.assert_has_calls(
            [mock.call("", **alerts._create_slack_publish_params(dcron_job, constants.Alert.FAILURE))]
        )

        self.assertEqual(models.DCronJobHistory.objects.filter(command_name=DUMMY_COMMAND).count(), 1)
        self._assert_history(dcron_job, constants.Alert.FAILURE)

    @mock.patch("sys.argv", ["manage.py", DUMMY_COMMAND])
    def test_pause_execution(self):
        class DummyCommand(commands.DCronCommand):
            called_1 = False
            called_2 = False

            def handle(self, *args, **options):
                self.called_1 = True
                super().handle(*args, **options)

            def _handle(self, *args, **options):
                self.called_2 = True

        dcron_job = models.DCronJob.objects.create(command_name=DUMMY_COMMAND)
        models.DCronJobSettings.objects.create(job=dcron_job, pause_execution=False, schedule="", full_command="")

        dummy_command = DummyCommand()
        dummy_command.execute(**{"no_color": None, "force_color": None, "stdout": None, "stderr": None})

        self.assertTrue(dummy_command.called_1)
        self.assertTrue(dummy_command.called_2)

        dcron_job.dcronjobsettings.pause_execution = True
        dcron_job.dcronjobsettings.save()

        dummy_command = DummyCommand()
        dummy_command.execute(**{"no_color": None, "force_color": None, "stdout": None, "stderr": None})

        self.assertTrue(dummy_command.called_1)
        self.assertFalse(dummy_command.called_2)

    @mock.patch("sys.argv", ["manage.py", DUMMY_COMMAND])
    @mock.patch("utils.metrics_compat.incr")
    @mock.patch("utils.metrics_compat.timing")
    def test_min_separation(self, mock_influx_timing, mock_influx_incr):
        class DummyCommand(commands.DCronCommand):
            def _handle(self, *args, **options):
                pass

        dummy_command = DummyCommand()

        now_dt = timezone.now()
        executed_dt = now_dt - datetime.timedelta(seconds=15)
        completed_dt = now_dt - datetime.timedelta(seconds=1)
        dcron_job = models.DCronJob.objects.create(
            command_name=DUMMY_COMMAND, executed_dt=executed_dt, completed_dt=completed_dt
        )
        models.DCronJobSettings.objects.create(job=dcron_job, schedule="", full_command="")

        with self.assertNumQueries(1):
            dummy_command.execute(**{"no_color": None, "force_color": None, "stdout": None, "stderr": None})

        mock_influx_incr.assert_has_calls([])
        self.assertEqual(len(mock_influx_timing.call_args_list), 0)

    @mock.patch("sys.argv", ["manage.py", DUMMY_COMMAND])
    @mock.patch("utils.metrics_compat.incr")
    @mock.patch("utils.metrics_compat.timing")
    @mock.patch("utils.pagerduty_helper._post_event")
    @mock.patch("utils.slack.publish")
    def test_recover_from_failure(self, mock_slack_publish, mock_post_event, mock_influx_timing, mock_influx_incr):
        event_1 = threading.Event()
        event_2 = threading.Event()
        event_3 = threading.Event()

        class DummyCommand(commands.DCronCommand):
            def handle(self, *args, **options):
                super().handle(*args, **options)
                event_3.set()

            def _handle(self, *args, **options):
                event_1.set()
                # Wait for failure alert check
                event_2.wait()

        dummy_command = DummyCommand()

        def run_command():
            dummy_command.execute(**{"no_color": None, "force_color": None, "stdout": None, "stderr": None})

        now_dt = timezone.now()
        executed_dt = now_dt - datetime.timedelta(seconds=45)
        completed_dt = now_dt - datetime.timedelta(seconds=42)
        dcron_job = models.DCronJob.objects.create(
            command_name=DUMMY_COMMAND,
            executed_dt=executed_dt,
            completed_dt=completed_dt,
            alert=constants.Alert.FAILURE,
        )
        models.DCronJobSettings.objects.create(job=dcron_job, schedule="0 * * * *", full_command="")

        command_thread = threading.Thread(target=run_command)

        try:
            command_thread.start()

            # Wait for job _handle to start (completed_dt set to None)
            event_1.wait()

            dcron_job.refresh_from_db()

            alert = alerts._check_alert(dcron_job)
            self.assertEqual(alert, constants.Alert.FAILURE)

            event_2.set()

            # Wait for job handle to complete (alert set to OK)
            event_3.wait()

            dcron_job.refresh_from_db()

            alert = alerts._check_alert(dcron_job)
            self.assertEqual(alert, constants.Alert.OK)

            mock_post_event.assert_has_calls(
                [
                    mock.call(
                        "resolve",
                        pagerduty_helper.PagerDutyEventType.Z1,
                        DUMMY_COMMAND,
                        alerts._alert_message(DUMMY_COMMAND, constants.Alert.OK),
                        event_severity=pagerduty_helper.PagerDutyEventSeverity.WARNING,
                        details=None,
                    )
                ]
            )

            mock_slack_publish.assert_has_calls(
                [mock.call("", **alerts._create_slack_publish_params(dcron_job, constants.Alert.OK))]
            )
        finally:
            event_2.set()

    @mock.patch("sys.argv", ["manage.py", DUMMY_COMMAND])
    @mock.patch("utils.metrics_compat.incr")
    @mock.patch("utils.metrics_compat.timing")
    @mock.patch("utils.pagerduty_helper._post_event")
    @mock.patch("utils.slack.publish")
    def test_recover_from_duration(self, mock_slack_publish, mock_post_event, mock_influx_timing, mock_influx_incr):
        event_1 = threading.Event()
        event_2 = threading.Event()
        event_3 = threading.Event()

        class DummyCommand(commands.DCronCommand):
            def handle(self, *args, **options):
                super().handle(*args, **options)
                event_3.set()

            def _handle(self, *args, **options):
                event_1.set()
                # Wait for failure alert check
                event_2.wait()

        dummy_command = DummyCommand()

        def run_command():
            dummy_command.execute(**{"no_color": None, "force_color": None, "stdout": None, "stderr": None})

        now_dt = timezone.now()
        executed_dt = now_dt - datetime.timedelta(seconds=45)
        completed_dt = now_dt - datetime.timedelta(seconds=42)
        dcron_job = models.DCronJob.objects.create(
            command_name=DUMMY_COMMAND,
            executed_dt=executed_dt,
            completed_dt=completed_dt,
            alert=constants.Alert.DURATION,
        )
        models.DCronJobSettings.objects.create(job=dcron_job, schedule="0 * * * *", full_command="")

        command_thread = threading.Thread(target=run_command)

        try:
            command_thread.start()

            # Wait for job _handle to start (completed_dt set to None)
            event_1.wait()

            dcron_job.refresh_from_db()

            alert = alerts._check_alert(dcron_job)
            self.assertEqual(alert, constants.Alert.DURATION)

            event_2.set()

            # Wait for job handle to complete (alert set to OK)
            event_3.wait()

            dcron_job.refresh_from_db()

            alert = alerts._check_alert(dcron_job)
            self.assertEqual(alert, constants.Alert.OK)

            mock_post_event.assert_has_calls(
                [
                    mock.call(
                        "resolve",
                        pagerduty_helper.PagerDutyEventType.Z1,
                        DUMMY_COMMAND,
                        alerts._alert_message(DUMMY_COMMAND, constants.Alert.OK),
                        event_severity=pagerduty_helper.PagerDutyEventSeverity.WARNING,
                        details=None,
                    )
                ]
            )

            mock_slack_publish.assert_has_calls(
                [mock.call("", **alerts._create_slack_publish_params(dcron_job, constants.Alert.OK))]
            )
        finally:
            event_2.set()

    @mock.patch("sys.argv", ["manage.py", DUMMY_COMMAND])
    @mock.patch("utils.metrics_compat.incr")
    @mock.patch("utils.metrics_compat.timing")
    @mock.patch("utils.pagerduty_helper._post_event")
    @mock.patch("utils.slack.publish")
    def test_recover_from_execution(self, mock_slack_publish, mock_post_event, mock_influx_timing, mock_influx_incr):
        event_1 = threading.Event()
        event_2 = threading.Event()
        event_3 = threading.Event()

        class DummyCommand(commands.DCronCommand):
            def handle(self, *args, **options):
                super().handle(*args, **options)
                event_3.set()

            def _handle(self, *args, **options):
                event_1.set()
                # Wait for failure alert check
                event_2.wait()

        dummy_command = DummyCommand()

        def run_command():
            dummy_command.execute(**{"no_color": None, "force_color": None, "stdout": None, "stderr": None})

        now_dt = timezone.now()
        executed_dt = now_dt - datetime.timedelta(seconds=45)
        completed_dt = now_dt - datetime.timedelta(seconds=42)
        dcron_job = models.DCronJob.objects.create(
            command_name=DUMMY_COMMAND,
            executed_dt=executed_dt,
            completed_dt=completed_dt,
            alert=constants.Alert.EXECUTION,
        )
        models.DCronJobSettings.objects.create(job=dcron_job, schedule="0 * * * *", full_command="")

        command_thread = threading.Thread(target=run_command)

        try:
            command_thread.start()

            # Wait for job _handle to start (completed_dt set to None)
            event_1.wait()

            dcron_job.refresh_from_db()

            alert = alerts._check_alert(dcron_job)
            self.assertEqual(alert, constants.Alert.EXECUTION)

            event_2.set()

            # Wait for job handle to complete (alert set to OK)
            event_3.wait()

            dcron_job.refresh_from_db()

            alert = alerts._check_alert(dcron_job)
            self.assertEqual(alert, constants.Alert.OK)

            mock_post_event.assert_has_calls(
                [
                    mock.call(
                        "resolve",
                        pagerduty_helper.PagerDutyEventType.Z1,
                        DUMMY_COMMAND,
                        alerts._alert_message(DUMMY_COMMAND, constants.Alert.OK),
                        event_severity=pagerduty_helper.PagerDutyEventSeverity.WARNING,
                        details=None,
                    )
                ]
            )

            mock_slack_publish.assert_has_calls(
                [mock.call("", **alerts._create_slack_publish_params(dcron_job, constants.Alert.OK))]
            )
        finally:
            event_2.set()
