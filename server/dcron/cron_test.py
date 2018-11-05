from django.conf import settings
from django.test import TestCase, override_settings

from dcron.exceptions import ParameterException
from dcron import models
from dcron import cron


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
#20 7,11 * * *    /home/ubuntu/docker-manage-py.sh audit_spend_integrity --slack
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
                    "schedule": "20 7,11 * * *",
                    "full_command": "/home/ubuntu/docker-manage-py.sh audit_spend_integrity --slack",
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
        "default_warning_wait": 60,
        "warning_waits": {"monitor_blacklists": 120, "refresh_etl": 3600},
    }
)
class DCronModelsTestCase(TestCase):
    crontab_example = (
        "0 9,12,15 * * *\t%s monitor_blacklists\n" % settings.DCRON["base_command"]
        + "15 9 * * *\t%s run_autopilot --daily-run\n" % settings.DCRON["base_command"]
        + "*/5 * * * *\t%s refresh_etl 3\n" % settings.DCRON["base_command"]
        + "#20 7,11 * * *\t%s audit_spend_integrity --slack\n" % settings.DCRON["base_command"]
    )

    def test_create_records(self):

        cron.process_crontab_items(file_contents=self.crontab_example)

        self.assertEqual(models.DCronJob.objects.count(), 4)
        self.assertEqual(models.DCronJobSettings.objects.count(), 4)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="monitor_blacklists")
        self.assertEqual(job_settings.job.command_name, "monitor_blacklists")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "0 9,12,15 * * *")
        self.assertEqual(job_settings.full_command, "%s monitor_blacklists" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, True)
        self.assertEqual(job_settings.warning_wait, 120)
        self.assertEqual(job_settings.manual_warning_wait, False)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="run_autopilot")
        self.assertEqual(job_settings.job.command_name, "run_autopilot")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "15 9 * * *")
        self.assertEqual(job_settings.full_command, "%s run_autopilot --daily-run" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, True)
        self.assertEqual(job_settings.warning_wait, 60)
        self.assertEqual(job_settings.manual_warning_wait, False)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="refresh_etl")
        self.assertEqual(job_settings.job.command_name, "refresh_etl")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "*/5 * * * *")
        self.assertEqual(job_settings.full_command, "%s refresh_etl 3" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, True)
        self.assertEqual(job_settings.warning_wait, 3600)
        self.assertEqual(job_settings.manual_warning_wait, False)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="audit_spend_integrity")
        self.assertEqual(job_settings.job.command_name, "audit_spend_integrity")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "20 7,11 * * *")
        self.assertEqual(job_settings.full_command, "%s audit_spend_integrity --slack" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, False)
        self.assertEqual(job_settings.warning_wait, 60)
        self.assertEqual(job_settings.manual_warning_wait, False)

    def test_update_records(self):
        dcj = models.DCronJob.objects.create(command_name="monitor_blacklists")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="5 9,12,15 * * *",
            full_command="%s monitor_blacklists" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["warning_waits"]["monitor_blacklists"],
        )

        dcj = models.DCronJob.objects.create(command_name="run_autopilot")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="15 9 * * *",
            full_command="%s run_autopilot --daily-run" % settings.DCRON["base_command"],
            enabled=False,
            warning_wait=settings.DCRON["default_warning_wait"],
        )

        dcj = models.DCronJob.objects.create(command_name="refresh_etl")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="*/5 * * * *",
            full_command="%s refresh_etl 3" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["warning_waits"]["refresh_etl"],
        )

        cron_item_generator = cron._crontab_items_iterator(file_contents=self.crontab_example)

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(3):
            # DCronJobSettings need to be updated.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="monitor_blacklists")
        self.assertEqual(job_settings.job.command_name, "monitor_blacklists")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "0 9,12,15 * * *")
        self.assertEqual(job_settings.full_command, "%s monitor_blacklists" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, True)
        self.assertEqual(job_settings.warning_wait, 120)
        self.assertEqual(job_settings.manual_warning_wait, False)

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(3):
            # DCronJobSettings need to be updated.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="run_autopilot")
        self.assertEqual(job_settings.job.command_name, "run_autopilot")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "15 9 * * *")
        self.assertEqual(job_settings.full_command, "%s run_autopilot --daily-run" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, True)
        self.assertEqual(job_settings.warning_wait, 60)
        self.assertEqual(job_settings.manual_warning_wait, False)

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(2):
            # Nothing needs to be done.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="refresh_etl")
        self.assertEqual(job_settings.job.command_name, "refresh_etl")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "*/5 * * * *")
        self.assertEqual(job_settings.full_command, "%s refresh_etl 3" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, True)
        self.assertEqual(job_settings.warning_wait, 3600)
        self.assertEqual(job_settings.manual_warning_wait, False)

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(6):
            # DCronJob and DCronJobSettings need to be created.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="audit_spend_integrity")
        self.assertEqual(job_settings.job.command_name, "audit_spend_integrity")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "20 7,11 * * *")
        self.assertEqual(job_settings.full_command, "%s audit_spend_integrity --slack" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, False)
        self.assertEqual(job_settings.warning_wait, 60)
        self.assertEqual(job_settings.manual_warning_wait, False)

    def test_remove_records(self):
        dcj = models.DCronJob.objects.create(command_name="monitor_blacklists")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="0 9,12,15 * * *",
            full_command="%s monitor_blacklists" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["warning_waits"]["monitor_blacklists"],
        )

        dcj = models.DCronJob.objects.create(command_name="run_autopilot")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="15 9 * * *",
            full_command="%s run_autopilot --daily-run" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["default_warning_wait"],
        )

        dcj = models.DCronJob.objects.create(command_name="refresh_etl")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="*/5 * * * *",
            full_command="%s refresh_etl 3" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["warning_waits"]["refresh_etl"],
        )

        dcj = models.DCronJob.objects.create(command_name="audit_spend_integrity")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="20 7,11 * * *",
            full_command="%s audit_spend_integrity --slack" % settings.DCRON["base_command"],
            enabled=False,
            warning_wait=settings.DCRON["default_warning_wait"],
        )

        dcj = models.DCronJob.objects.create(command_name="delete_me_1")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="10 *,* * * *",
            full_command="%s delete_me_1" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=settings.DCRON["default_warning_wait"],
        )

        dcj = models.DCronJob.objects.create(command_name="delete_me_2")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="8 *,* * * *",
            full_command="%s delete_me_2" % settings.DCRON["base_command"],
            enabled=False,
            warning_wait=settings.DCRON["default_warning_wait"],
        )

        dcj = models.DCronJob.objects.create(command_name="unregistered_command")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="4 *,* * * *",
            full_command="%s unregistered_command" % settings.DCRON["base_command"],
            enabled=False,
            warning_wait=settings.DCRON["default_warning_wait"],
        )

        crontab_example = self.crontab_example + "4 * * * *\t%s unregistered_command\n" % settings.DCRON["base_command"]

        cron.process_crontab_items(file_contents=crontab_example)

        self.assertEqual(models.DCronJob.objects.count(), 4)
        self.assertEqual(models.DCronJobSettings.objects.count(), 4)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="monitor_blacklists")
        self.assertEqual(job_settings.job.command_name, "monitor_blacklists")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "0 9,12,15 * * *")
        self.assertEqual(job_settings.full_command, "%s monitor_blacklists" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, True)
        self.assertEqual(job_settings.warning_wait, 120)
        self.assertEqual(job_settings.manual_warning_wait, False)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="run_autopilot")
        self.assertEqual(job_settings.job.command_name, "run_autopilot")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "15 9 * * *")
        self.assertEqual(job_settings.full_command, "%s run_autopilot --daily-run" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, True)
        self.assertEqual(job_settings.warning_wait, 60)
        self.assertEqual(job_settings.manual_warning_wait, False)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="refresh_etl")
        self.assertEqual(job_settings.job.command_name, "refresh_etl")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "*/5 * * * *")
        self.assertEqual(job_settings.full_command, "%s refresh_etl 3" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, True)
        self.assertEqual(job_settings.warning_wait, 3600)
        self.assertEqual(job_settings.manual_warning_wait, False)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="audit_spend_integrity")
        self.assertEqual(job_settings.job.command_name, "audit_spend_integrity")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "20 7,11 * * *")
        self.assertEqual(job_settings.full_command, "%s audit_spend_integrity --slack" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, False)
        self.assertEqual(job_settings.warning_wait, 60)
        self.assertEqual(job_settings.manual_warning_wait, False)

    def test_manual_warning_wait(self):
        dcj = models.DCronJob.objects.create(command_name="monitor_blacklists")
        models.DCronJobSettings.objects.create(
            job=dcj,
            schedule="0 9,12,15 * * *",
            full_command="%s monitor_blacklists" % settings.DCRON["base_command"],
            enabled=True,
            warning_wait=600,
            manual_warning_wait=True,
        )

        cron_item_generator = cron._crontab_items_iterator(file_contents=self.crontab_example)

        cron_item = next(cron_item_generator)

        with self.assertNumQueries(2):
            # Nothing needs to be done.
            cron._process_cron_item(cron_item)

        job_settings = models.DCronJobSettings.objects.get(job__command_name="monitor_blacklists")
        self.assertEqual(job_settings.job.command_name, "monitor_blacklists")
        self.assertEqual(job_settings.job.executed_dt, None)
        self.assertEqual(job_settings.job.completed_dt, None)
        self.assertEqual(job_settings.job.host, None)
        self.assertEqual(job_settings.schedule, "0 9,12,15 * * *")
        self.assertEqual(job_settings.full_command, "%s monitor_blacklists" % settings.DCRON["base_command"])
        self.assertEqual(job_settings.enabled, True)
        self.assertEqual(job_settings.warning_wait, 600)
        self.assertEqual(job_settings.manual_warning_wait, True)
