from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from django.test import override_settings

from dcron import constants
from dcron import cron
from dcron import models
from dcron.exceptions import ParameterException


class CrontabItemsGeneratorTestCase(TestCase):
    def test_no_args(self):
        with self.assertRaises(ParameterException):
            for _ in cron._crontab_items_iterator():
                pass

    def test_both_none(self):
        with self.assertRaises(ParameterException):
            for _ in cron._crontab_items_iterator(file_name=None, file_contents=None):
                pass

    def test_both_empty(self):
        with self.assertRaises(ParameterException):
            for _ in cron._crontab_items_iterator(file_name="", file_contents=""):
                pass

    def test_crontab_example(self):
        crontab_example = """
# Some comments

0 9,12,15 * * *  /home/ubuntu/docker-manage-py.sh monitor_blacklists
15 9 * * *       /home/ubuntu/docker-manage-py.sh run_autopilot --daily-run
*/5 * * * *      /home/ubuntu/docker-manage-py.sh refresh_etl 3
10 9-20 * * *    /home/ubuntu/docker-manage-py.sh send_scheduled_reports
0 * * * *        /home/ubuntu/docker-manage-py.sh monitor_selfmanaged
#Some more comments
0 7 * * 1        /home/ubuntu/docker-manage-py.sh send_weekly_reports
#20 11 * * *      /home/ubuntu/docker-manage-py.sh audit_hacks --slack
0 0 * * *        /home/ubuntu/docker-manage-py.sh cleartokens
*/1 * * * *      /home/ubuntu/docker-manage-py.sh handle_auto_save_batches
# Test non-standard definitions
@hourly          /home/ubuntu/docker-manage-py.sh monitor_hourly
@daily          /home/ubuntu/docker-manage-py.sh monitor_daily
@weekly          /home/ubuntu/docker-manage-py.sh monitor_weekly
@monthly          /home/ubuntu/docker-manage-py.sh monitor_monthly
@yearly          /home/ubuntu/docker-manage-py.sh monitor_yearly
@annually          /home/ubuntu/docker-manage-py.sh monitor_annually
@midnight          /home/ubuntu/docker-manage-py.sh monitor_midnight
@reboot          /home/ubuntu/docker-manage-py.sh monitor_reboot

# Final remarks
"""

        kwargs_list = []
        for cron_item in cron._crontab_items_iterator(file_contents=crontab_example):
            kwargs_list.append(cron._dcron_job_settings_kwargs(cron_item))

        self.assertEqual(
            kwargs_list,
            [
                {
                    "schedule": "0 9,12,15 * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh monitor_blacklists",
                    "enabled": True,
                },
                {
                    "schedule": "15 9 * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh run_autopilot --daily-run",
                    "enabled": True,
                },
                {
                    "schedule": "*/5 * * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh refresh_etl 3",
                    "enabled": True,
                },
                {
                    "schedule": "10 9-20 * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh send_scheduled_reports",
                    "enabled": True,
                },
                {
                    "schedule": "0 * * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh monitor_selfmanaged",
                    "enabled": True,
                },
                {
                    "schedule": "0 7 * * 1",
                    "full_command": "/home/ubuntu/docker-manage-py.sh send_weekly_reports",
                    "enabled": True,
                },
                {
                    "schedule": "20 11 * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh audit_hacks --slack",
                    "enabled": False,
                },
                {
                    "schedule": "0 0 * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh cleartokens",
                    "enabled": True,
                },
                {
                    "schedule": "* * * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh handle_auto_save_batches",
                    "enabled": True,
                },
                {
                    "schedule": "0 * * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh monitor_hourly",
                    "enabled": True,
                },
                {
                    "schedule": "0 0 * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh monitor_daily",
                    "enabled": True,
                },
                {
                    "schedule": "0 0 * * 0",
                    "full_command": "/home/ubuntu/docker-manage-py.sh monitor_weekly",
                    "enabled": True,
                },
                {
                    "schedule": "0 0 1 * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh monitor_monthly",
                    "enabled": True,
                },
                {
                    "schedule": "0 0 1 1 *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh monitor_yearly",
                    "enabled": True,
                },
                {
                    "schedule": "0 0 1 1 *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh monitor_annually",
                    "enabled": True,
                },
                {
                    "schedule": "0 0 * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh monitor_midnight",
                    "enabled": True,
                },
                {
                    "schedule": "* * * * *",  # TODO is this OK?
                    "full_command": "/home/ubuntu/docker-manage-py.sh monitor_reboot",
                    "enabled": True,
                },
            ],
        )


@override_settings(
    DCRON={
        "base_command": "/home/ubuntu/docker-manage-py.sh",
        "check_margin": timedelta(seconds=5),
        "default_warning_wait": 60,
        "warning_waits": {"monitor_blacklists": 120, "refresh_etl": 3600},
        "default_max_duration": 3600,
        "max_durations": {},
    }
)
class DCronModelsTestCase(TestCase):
    crontab_example = (
        "0 9,12,15 * * *\t%s monitor_blacklists\n" % settings.DCRON["base_command"]
        + "15 9 * * *\t%s run_autopilot --daily-run\n" % settings.DCRON["base_command"]
        + "*/5 * * * *\t%s refresh_etl 3\n" % settings.DCRON["base_command"]
        + "#20 11 * * *\t%s audit_hacks --slack\n" % settings.DCRON["base_command"]
    )

    def _assert_job_settings(
        self,
        job_settings,
        command_name,
        schedule,
        enabled,
        warning_wait,
        max_duration,
        manual_override,
        extra_params="",
    ):
        full_command = "%s %s%s" % (settings.DCRON["base_command"], command_name, extra_params)
        self.assertEqual(job_settings.job.command_name, command_name)
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.job.alert, constants.Alert.OK)
        self.assertEqual(job_settings.schedule, schedule)
        self.assertEqual(job_settings.full_command, full_command)
        self.assertEqual(job_settings.enabled, enabled)
        self.assertEqual(job_settings.warning_wait, warning_wait)
        self.assertEqual(job_settings.max_duration, max_duration)
        self.assertEqual(job_settings.manual_override, manual_override)

    def test_create_records(self):

        cron.process_crontab_items(file_contents=self.crontab_example)

        self.assertEqual(models.DCronJob.objects.count(), 4)
        self.assertEqual(models.DCronJobSettings.objects.count(), 4)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="monitor_blacklists")
        self._assert_job_settings(job_settings, "monitor_blacklists", "0 9,12,15 * * *", True, 120, 3600, False)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="run_autopilot")
        self._assert_job_settings(
            job_settings, "run_autopilot", "15 9 * * *", True, 60, 3600, False, extra_params=" --daily-run"
        )

        job_settings = models.DCronJobSettings.objects.get(job__command_name="refresh_etl")
        self._assert_job_settings(
            job_settings, "refresh_etl", "*/5 * * * *", True, 3600, 3600, False, extra_params=" 3"
        )

        job_settings = models.DCronJobSettings.objects.get(job__command_name="audit_hacks")
        self._assert_job_settings(
            job_settings, "audit_hacks", "20 11 * * *", False, 60, 3600, False, extra_params=" --slack"
        )

    def test_update_records(self):
        dcj = models.DCronJob.objects.create(command_name="monitor_blacklists")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="5 9,12,15 * * *",
            full_command="%s monitor_blacklists" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["warning_waits"]["monitor_blacklists"],
            max_duration=3600,
        )

        dcj = models.DCronJob.objects.create(command_name="run_autopilot")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="15 9 * * *",
            full_command="%s run_autopilot --daily-run" % settings.DCRON["base_command"],
            enabled=False,
            warning_wait=settings.DCRON["default_warning_wait"],
            max_duration=600,
        )

        dcj = models.DCronJob.objects.create(command_name="refresh_etl")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="*/5 * * * *",
            full_command="%s refresh_etl 3" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["warning_waits"]["refresh_etl"],
            max_duration=3600,
        )

        cron_item_generator = cron._crontab_items_iterator(file_contents=self.crontab_example)

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(3):
            # DCronJobSettings need to be updated.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="monitor_blacklists")
        self._assert_job_settings(job_settings, "monitor_blacklists", "0 9,12,15 * * *", True, 120, 3600, False)

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(3):
            # DCronJobSettings need to be updated.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="run_autopilot")
        self._assert_job_settings(
            job_settings, "run_autopilot", "15 9 * * *", True, 60, 3600, False, extra_params=" --daily-run"
        )

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(2):
            # Nothing needs to be done.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="refresh_etl")
        self._assert_job_settings(
            job_settings, "refresh_etl", "*/5 * * * *", True, 3600, 3600, False, extra_params=" 3"
        )

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(6):
            # DCronJob and DCronJobSettings need to be created.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="audit_hacks")
        self._assert_job_settings(
            job_settings, "audit_hacks", "20 11 * * *", False, 60, 3600, False, extra_params=" --slack"
        )

    def test_remove_records(self):
        dcj = models.DCronJob.objects.create(command_name="monitor_blacklists")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="0 9,12,15 * * *",
            full_command="%s monitor_blacklists" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["warning_waits"]["monitor_blacklists"],
            max_duration=3600,
        )

        dcj = models.DCronJob.objects.create(command_name="run_autopilot")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="15 9 * * *",
            full_command="%s run_autopilot --daily-run" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["default_warning_wait"],
            max_duration=3600,
        )

        dcj = models.DCronJob.objects.create(command_name="refresh_etl")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="*/5 * * * *",
            full_command="%s refresh_etl 3" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["warning_waits"]["refresh_etl"],
            max_duration=3600,
        )

        dcj = models.DCronJob.objects.create(command_name="audit_hacks")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="20 11 * * *",
            full_command="%s audit_hacks --slack" % settings.DCRON["base_command"],
            enabled=False,
            warning_wait=settings.DCRON["default_warning_wait"],
            max_duration=3600,
        )

        dcj = models.DCronJob.objects.create(command_name="delete_me_1")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="10 *,* * * *",
            full_command="%s delete_me_1" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["default_warning_wait"],
            max_duration=3600,
        )

        dcj = models.DCronJob.objects.create(command_name="delete_me_2")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="8 *,* * * *",
            full_command="%s delete_me_2" % settings.DCRON["base_command"],
            enabled=False,
            warning_wait=settings.DCRON["default_warning_wait"],
            max_duration=3600,
        )

        dcj = models.DCronJob.objects.create(command_name="unregistered_command")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="4 *,* * * *",
            full_command="%s unregistered_command" % settings.DCRON["base_command"],
            enabled=False,
            warning_wait=settings.DCRON["default_warning_wait"],
            max_duration=3600,
        )

        crontab_example = self.crontab_example + "4 * * * *\t%s unregistered_command\n" % settings.DCRON["base_command"]

        cron.process_crontab_items(file_contents=crontab_example)

        self.assertEqual(models.DCronJob.objects.count(), 4)
        self.assertEqual(models.DCronJobSettings.objects.count(), 4)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="monitor_blacklists")
        self._assert_job_settings(job_settings, "monitor_blacklists", "0 9,12,15 * * *", True, 120, 3600, False)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="run_autopilot")
        self._assert_job_settings(
            job_settings, "run_autopilot", "15 9 * * *", True, 60, 3600, False, extra_params=" --daily-run"
        )

        job_settings = models.DCronJobSettings.objects.get(job__command_name="refresh_etl")
        self._assert_job_settings(
            job_settings, "refresh_etl", "*/5 * * * *", True, 3600, 3600, False, extra_params=" 3"
        )

        job_settings = models.DCronJobSettings.objects.get(job__command_name="audit_hacks")
        self._assert_job_settings(
            job_settings, "audit_hacks", "20 11 * * *", False, 60, 3600, False, extra_params=" --slack"
        )

    def test_manual_override(self):
        dcj = models.DCronJob.objects.create(command_name="monitor_blacklists")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="0 9,12,15 * * *",
            full_command="%s monitor_blacklists" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=600,
            max_duration=600,
            manual_override=True,
        )

        cron_item_generator = cron._crontab_items_iterator(file_contents=self.crontab_example)

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(2):
            # Nothing needs to be done.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="monitor_blacklists")
        self._assert_job_settings(job_settings, "monitor_blacklists", "0 9,12,15 * * *", True, 600, 600, True)

    def test_change_warning_wait(self):
        dcj = models.DCronJob.objects.create(command_name="monitor_blacklists")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="0 9,12,15 * * *",
            full_command="%s monitor_blacklists" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=600,
            max_duration=3600,
        )

        cron_item_generator = cron._crontab_items_iterator(file_contents=self.crontab_example)

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(3):
            # DCronJobSettings need to be updated.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="monitor_blacklists")
        self._assert_job_settings(job_settings, "monitor_blacklists", "0 9,12,15 * * *", True, 120, 3600, False)

    def test_change_max_duration(self):
        dcj = models.DCronJob.objects.create(command_name="monitor_blacklists")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="0 9,12,15 * * *",
            full_command="%s monitor_blacklists" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=600,
            max_duration=600,
        )

        cron_item_generator = cron._crontab_items_iterator(file_contents=self.crontab_example)

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(3):
            # DCronJobSettings need to be updated.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="monitor_blacklists")
        self._assert_job_settings(job_settings, "monitor_blacklists", "0 9,12,15 * * *", True, 120, 3600, False)
