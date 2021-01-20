import sys

import mock
from django.conf import settings
from django.core.management import BaseCommand
from django.core.management import CommandError
from django.test import TransactionTestCase

from dcron import constants
from dcron import models
from dcron.management.commands import dcron_launcher


class DCronLauncherTestCase(TransactionTestCase):
    """
    Test dcron_launcher management command - a proxy to another management command that does not extend
    DCronCommand.
    """

    class OtherCommand(BaseCommand):
        def add_arguments(self, parser):
            parser.add_argument("arg0")
            parser.add_argument("--arg1", default=0)
            parser.add_argument("--arg2", action="store_true")

        def handle(self, *args, **options):
            self.args = args
            self.options = options

    other_command = OtherCommand()

    @mock.patch("sys.argv", ["manage.py", "dcron_launcher", "othercommand", "foo", "--arg1=5", "--arg2"])
    @mock.patch("django.core.management.get_commands", return_value={"othercommand": "test.foo"})
    @mock.patch("django.core.management.load_command_class", return_value=other_command)
    @mock.patch("utils.metrics_compat.incr")
    @mock.patch("utils.metrics_compat.timing")
    def test_launcher(self, mock_influx_timing, mock_influx_incr, mock_load_command_class, mock_get_commands):
        launcher_command = dcron_launcher.Command()

        launcher_command.execute(
            *sys.argv[2:], **{"no_color": None, "force_color": None, "stdout": None, "stderr": None}
        )

        dcron_job_qs = models.DCronJob.objects.filter(command_name="othercommand")

        self.assertEqual(dcron_job_qs.count(), 1)

        dcron_job = dcron_job_qs.get()
        self.assertIsNotNone(dcron_job.executed_dt)
        self.assertIsNotNone(dcron_job.completed_dt)
        self.assertEqual(dcron_job.host, settings.HOSTNAME)
        self.assertEqual(dcron_job.alert, constants.Alert.OK)

        mock_influx_incr.assert_has_calls([mock.call("dcron_command_count", 1, command_name="othercommand")])

        call_args_list = mock_influx_timing.call_args_list
        self.assertEqual(len(call_args_list), 1)
        self.assertEqual(call_args_list[0][0][0], "dcron_command_duration")
        self.assertDictEqual(call_args_list[0][1], {"command_name": "othercommand"})

        self.assertEqual(DCronLauncherTestCase.other_command.args, tuple())
        self.assertEqual(
            DCronLauncherTestCase.other_command.options,
            {
                "arg0": "foo",
                "arg1": "5",
                "arg2": True,
                "no_color": False,
                "force_color": False,
                "pythonpath": None,
                "settings": None,
                "traceback": False,
                "verbosity": 1,
                "skip_checks": True,
            },
        )

    @mock.patch("sys.argv", ["manage.py", "dcron_launcher", "dcron_launcher"])
    def test_recursion(self):
        with self.assertRaises(CommandError):
            dcron_launcher.Command()
