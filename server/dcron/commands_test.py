import socket
import threading

import mock
from django.conf import settings
from django.test import TestCase
from django.test import TransactionTestCase

import django_pglocks
from dcron import alerts
from dcron import commands
from dcron import constants
from dcron import exceptions
from dcron import models
from dcron.commands import DCronCommand
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

    @mock.patch("sys.argv", ["manage.py", DUMMY_COMMAND])
    @mock.patch("influx.incr")
    @mock.patch("influx.timing")
    def test_handle(self, mock_influx_timing, mock_influx_incr):

        event_1 = threading.Event()
        event_2 = threading.Event()
        event_3 = threading.Event()

        class DummyCommand(DCronCommand):
            def handle(self, *args, **options):
                super().handle(*args, **options)
                event_3.set()

            def _handle(self, *args, **options):
                event_1.set()
                event_2.wait()

        dummy_command = DummyCommand()

        def run_command():
            dummy_command.execute(**{"no_color": None, "stdout": None, "stderr": None})

        dcron_job_qs = models.DCronJob.objects.filter(command_name=DUMMY_COMMAND)

        self.assertEqual(dcron_job_qs.count(), 0)

        command_thread = threading.Thread(target=run_command)
        command_thread.start()

        event_1.wait()  # Wait until DummyCommand._handle starts running.

        mock_influx_incr.assert_has_calls([mock.call("dcron_command_count", 1, command_name=DUMMY_COMMAND)])

        self.assertEqual(dcron_job_qs.count(), 1)

        dcron_job = dcron_job_qs.get()
        self.assertIsNotNone(dcron_job.executed_dt)
        self.assertIsNone(dcron_job.completed_dt)
        self.assertEqual(dcron_job.host, socket.gethostname())
        self.assertEqual(dcron_job.alert, constants.Alert.OK)

        try:
            with django_pglocks.advisory_lock(DUMMY_COMMAND, wait=False) as acquired:
                self.assertFalse(acquired)

            self.assertEqual(dcron_job_qs.count(), 1)

            dcron_job = dcron_job_qs.get()
            self.assertIsNotNone(dcron_job.executed_dt)
            self.assertIsNone(dcron_job.completed_dt)
            self.assertEqual(dcron_job.host, socket.gethostname())
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
        self.assertEqual(dcron_job.host, socket.gethostname())
        self.assertEqual(dcron_job.alert, constants.Alert.OK)

        with django_pglocks.advisory_lock(DUMMY_COMMAND, wait=False) as acquired:
            self.assertTrue(acquired)

    @mock.patch("sys.argv", ["manage.py", DUMMY_COMMAND])
    @mock.patch("influx.incr")
    @mock.patch("influx.timing")
    @mock.patch("utils.pagerduty_helper._post_event")
    def test_failure(self, mock_post_event, mock_influx_timing, mock_influx_incr):
        class DummyCommand(DCronCommand):
            def _handle(self, *args, **options):
                raise RuntimeError("TEST!")

        dummy_command = DummyCommand()

        dummy_command.execute(**{"no_color": None, "stdout": None, "stderr": None})

        dcron_job_qs = models.DCronJob.objects.filter(command_name=DUMMY_COMMAND)

        self.assertEqual(dcron_job_qs.count(), 1)

        dcron_job = dcron_job_qs.get()
        self.assertIsNotNone(dcron_job.executed_dt)
        self.assertIsNotNone(dcron_job.completed_dt)
        self.assertEqual(dcron_job.host, socket.gethostname())
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
                    details=None,
                )
            ]
        )
