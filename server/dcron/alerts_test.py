import datetime

from django.conf import settings
from django.test import TestCase
from django.test import override_settings
from mock import mock

from dcron import alerts
from dcron import constants
from dcron import models
from utils import dates_helper
from utils import pagerduty_helper


def _get_rounded_now(minute=0, second=0):
    dt = dates_helper.utc_now()
    dt = dt.replace(minute=minute, second=second, microsecond=0)
    return dt


def _create_job(command_name, job_kwargs_dict, settings_kwargs_dict):
    full_command = "%s %s" % (settings.DCRON["base_command"], command_name)

    dcron_job = models.DCronJob.objects.create(command_name=command_name, **job_kwargs_dict)

    if settings_kwargs_dict:
        settings_kwargs_dict.setdefault("warning_wait", settings.DCRON["default_warning_wait"])
        settings_kwargs_dict.setdefault(
            "max_duration", settings.DCRON["max_durations"].get(command_name, settings.DCRON["default_max_duration"])
        )
        settings_kwargs_dict.setdefault(
            "min_separation",
            settings.DCRON["min_separations"].get(command_name, settings.DCRON["default_min_separation"]),
        )

        models.DCronJobSettings.objects.create(job=dcron_job, full_command=full_command, **settings_kwargs_dict)

    return dcron_job


@override_settings(
    DCRON={
        "base_command": "/home/ubuntu/docker-manage-py.sh",
        "check_margin": datetime.timedelta(seconds=5),
        "severities": {},
        "default_warning_wait": 60,
        "warning_waits": {"some_command": 600},
        "default_max_duration": 3600,
        "max_durations": {},
        "default_min_separation": 30,
        "min_separations": {},
    }
)
class CheckAlertsExecutionTimesTestCase(TestCase):
    """
    Check a single job at different times according to cron schedule times.

    The name of the test function defines the condition "test_<check_execution>_<relative_to_scheduled>[_<extra)]":
    <check_execution> defines when check is executed relative to scheduled cron execution
    <relative_to_scheduled> defines when cron job executed relative to scheduled cron execution
    <extra> extra conditions where needed
    """

    @staticmethod
    def _create_some_job(executed_dt, no_settings=False):
        completed_dt = executed_dt + datetime.timedelta(seconds=3) if executed_dt else None
        job_kwargs_dict = {"executed_dt": executed_dt, "completed_dt": completed_dt}
        if no_settings:
            settings_kwargs_dict = None
        else:
            settings_kwargs_dict = {
                "schedule": "0 * * * *",
                "enabled": True,
                "warning_wait": settings.DCRON["warning_waits"]["some_command"],
            }

        return _create_job("some command", job_kwargs_dict, settings_kwargs_dict)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now())
    def test_exact_on_time(self, mock_now):
        job = self._create_some_job(dates_helper.utc_now())
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now())
    def test_exact_just_before_scheduled(self, mock_now):
        job = self._create_some_job(dates_helper.utc_now() - settings.DCRON["check_margin"] / 2)
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now())
    def test_exact_just_after_scheduled(self, mock_now):
        job = self._create_some_job(dates_helper.utc_now() + settings.DCRON["check_margin"] / 2)
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now())
    def test_exact_before_scheduled(self, mock_now):
        job = self._create_some_job(dates_helper.utc_now() - 2 * settings.DCRON["check_margin"])
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now())
    def test_exact_after_scheduled(self, mock_now):
        job = self._create_some_job(dates_helper.utc_now() + 2 * settings.DCRON["check_margin"])
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=5))
    def test_ok_just_before_scheduled(self, mock_now):
        job = self._create_some_job(
            dates_helper.utc_now() - datetime.timedelta(minutes=5) - settings.DCRON["check_margin"] / 2
        )
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=5))
    def test_ok_just_after_scheduled(self, mock_now):
        job = self._create_some_job(
            dates_helper.utc_now() - datetime.timedelta(minutes=5) + settings.DCRON["check_margin"] / 2
        )
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=5))
    def test_ok_before_scheduled(self, mock_now):
        job = self._create_some_job(
            dates_helper.utc_now() - datetime.timedelta(minutes=5) - 2 * settings.DCRON["check_margin"]
        )
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=5))
    def test_ok_after_scheduled(self, mock_now):
        job = self._create_some_job(
            dates_helper.utc_now() - datetime.timedelta(minutes=5) + 2 * settings.DCRON["check_margin"]
        )
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=15))
    def test_warning_just_before_scheduled(self, mock_now):
        job = self._create_some_job(
            dates_helper.utc_now() - datetime.timedelta(minutes=15) - settings.DCRON["check_margin"] / 2
        )
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=15))
    def test_warning_just_after_scheduled(self, mock_now):
        job = self._create_some_job(
            dates_helper.utc_now() - datetime.timedelta(minutes=15) + settings.DCRON["check_margin"] / 2
        )
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=15))
    def test_warning_before_scheduled(self, mock_now):
        job = self._create_some_job(
            dates_helper.utc_now() - datetime.timedelta(minutes=15) - 2 * settings.DCRON["check_margin"]
        )
        self.assertEqual(alerts._check_alert(job), constants.Alert.EXECUTION)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=15))
    def test_warning_after_scheduled(self, mock_now):
        job = self._create_some_job(
            dates_helper.utc_now() - datetime.timedelta(minutes=15) + 2 * settings.DCRON["check_margin"]
        )
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=15))
    def test_warning_before_scheduled_no_settings(self, mock_now):
        job = self._create_some_job(
            dates_helper.utc_now() - datetime.timedelta(minutes=15) - 2 * settings.DCRON["check_margin"],
            no_settings=True,
        )
        # There should be no alert in case of missing DCronJobSettings.
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=15))
    def test_warning_before_scheduled_no_executed_dt(self, mock_now):
        job = self._create_some_job(None)
        # There should be no alert in case of executed_dt equals None.
        self.assertEqual(alerts._check_alert(job), constants.Alert.OK)


@override_settings(
    DCRON={
        "base_command": "/home/ubuntu/docker-manage-py.sh",
        "check_margin": datetime.timedelta(seconds=5),
        "severities": {},
        "default_warning_wait": 600,
        "warning_waits": {},
        "default_max_duration": 7200,
        "max_durations": {"command_08": 3600, "command_09": 3600, "command_19": 3600},
        "default_min_separation": 30,
        "min_separations": {},
    }
)
class CheckAlertsTestCase(TestCase):
    @staticmethod
    def _get_dcron_job_alerts():
        dcron_job_alerts = []
        dcron_jobs = models.DCronJob.objects.filter(dcronjobsettings__enabled=True)

        for dcron_job in dcron_jobs:
            alert = alerts._check_alert(dcron_job)
            if alert != constants.Alert.OK:
                dcron_job_alerts.append({"job": dcron_job, "alert": alert})

        return dcron_job_alerts

    def _assert_dcronjobalert(self, dcron_job_alert, command_name, alert):
        self.assertEqual(dcron_job_alert["job"].command_name, command_name)
        self.assertEqual(dcron_job_alert["alert"], alert)

    def test_no_dcron_jobs(self):
        self.assertEqual(len(self._get_dcron_job_alerts()), 0)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=17, second=3))
    def test_many_dcron_jobs(self, mock_now):
        # Executed in time.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=15),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=14, seconds=57),
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_01", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=21),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=20, seconds=57),
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_02", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution, but alerting already.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=21),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=20, seconds=57),
            "alert": constants.Alert.EXECUTION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_03", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution, but disabled.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=21),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=20, seconds=57),
        }
        settings_kwargs_dict = {"schedule": "0 * * * *", "enabled": False}
        _create_job("command_04", job_kwargs_dict, settings_kwargs_dict)

        # Not yet executed.
        job_kwargs_dict = {"executed_dt": None, "completed_dt": None}
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_05", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution and outside check margin.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=90),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=89, seconds=57),
        }
        settings_kwargs_dict = {"schedule": "18 * * * *"}
        _create_job("command_06", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution, but inside check margin.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=90),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=89, seconds=57),
        }
        settings_kwargs_dict = {"schedule": "17 * * * *"}
        _create_job("command_07", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution and outside check margin, exceeded max_duration.
        job_kwargs_dict = {"executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=90), "completed_dt": None}
        settings_kwargs_dict = {"schedule": "18 * * * *"}
        _create_job("command_08", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution, but inside check margin, exceeded max_duration.
        job_kwargs_dict = {"executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=90), "completed_dt": None}
        settings_kwargs_dict = {"schedule": "17 * * * *"}
        _create_job("command_09", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution, but no settings.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=90),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=89, seconds=57),
        }
        settings_kwargs_dict = None
        _create_job("command_10", job_kwargs_dict, settings_kwargs_dict)

        # Exceeded max duration, but no settings.
        job_kwargs_dict = {"executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=90), "completed_dt": None}
        settings_kwargs_dict = None
        _create_job("command_11", job_kwargs_dict, settings_kwargs_dict)

        # Executed in time, not yet completed.
        job_kwargs_dict = {"executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=15), "completed_dt": None}
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_12", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution, not yet completed.
        job_kwargs_dict = {"executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=21), "completed_dt": None}
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_13", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution, alerting already, not yet completed.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=21),
            "completed_dt": None,
            "alert": constants.Alert.EXECUTION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_14", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution, but disabled, not yet completed.
        job_kwargs_dict = {"executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=21), "completed_dt": None}
        settings_kwargs_dict = {"schedule": "0 * * * *", "enabled": False}
        _create_job("command_15", job_kwargs_dict, settings_kwargs_dict)

        dcron_job_alerts = self._get_dcron_job_alerts()
        self.assertEqual(len(dcron_job_alerts), 6)
        self._assert_dcronjobalert(dcron_job_alerts[0], "command_02", constants.Alert.EXECUTION)
        self._assert_dcronjobalert(dcron_job_alerts[1], "command_03", constants.Alert.EXECUTION)
        self._assert_dcronjobalert(dcron_job_alerts[2], "command_06", constants.Alert.EXECUTION)
        self._assert_dcronjobalert(dcron_job_alerts[3], "command_08", constants.Alert.DURATION)
        self._assert_dcronjobalert(dcron_job_alerts[4], "command_09", constants.Alert.DURATION)
        self._assert_dcronjobalert(dcron_job_alerts[5], "command_14", constants.Alert.EXECUTION)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=17, second=3))
    def test_failure_normal_execution(self, mock_now):
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=16),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=15),
            "alert": constants.Alert.FAILURE,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_01", job_kwargs_dict, settings_kwargs_dict)

        dcron_job_alerts = self._get_dcron_job_alerts()
        self.assertEqual(len(dcron_job_alerts), 1)
        self._assert_dcronjobalert(dcron_job_alerts[0], "command_01", constants.Alert.FAILURE)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=17, second=3))
    def test_failure_late_execution(self, mock_now):
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=2),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=1),
            "alert": constants.Alert.FAILURE,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_01", job_kwargs_dict, settings_kwargs_dict)

        dcron_job_alerts = self._get_dcron_job_alerts()
        self.assertEqual(len(dcron_job_alerts), 1)
        self._assert_dcronjobalert(dcron_job_alerts[0], "command_01", constants.Alert.FAILURE)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=17, second=3))
    def test_failure_missed_execution(self, mock_now):
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(hours=2, minutes=16),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(hours=2, minutes=15),
            "alert": constants.Alert.FAILURE,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_01", job_kwargs_dict, settings_kwargs_dict)

        dcron_job_alerts = self._get_dcron_job_alerts()
        self.assertEqual(len(dcron_job_alerts), 1)
        self._assert_dcronjobalert(dcron_job_alerts[0], "command_01", constants.Alert.FAILURE)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=17, second=3))
    def test_execution_missed_execution(self, mock_now):
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(hours=2, minutes=16),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(hours=2, minutes=15),
            "alert": constants.Alert.EXECUTION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_01", job_kwargs_dict, settings_kwargs_dict)

        dcron_job_alerts = self._get_dcron_job_alerts()
        self.assertEqual(len(dcron_job_alerts), 1)
        self._assert_dcronjobalert(dcron_job_alerts[0], "command_01", constants.Alert.EXECUTION)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=17, second=3))
    def test_duration_missed_execution(self, mock_now):
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(hours=2, minutes=16),
            "completed_dt": None,
            "alert": constants.Alert.DURATION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_01", job_kwargs_dict, settings_kwargs_dict)

        dcron_job_alerts = self._get_dcron_job_alerts()
        self.assertEqual(len(dcron_job_alerts), 1)
        self._assert_dcronjobalert(dcron_job_alerts[0], "command_01", constants.Alert.DURATION)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=17, second=3))
    def test_execution_in_progress(self, mock_now):
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=1),
            "completed_dt": None,
            "alert": constants.Alert.EXECUTION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_01", job_kwargs_dict, settings_kwargs_dict)

        dcron_job_alerts = self._get_dcron_job_alerts()
        self.assertEqual(len(dcron_job_alerts), 1)
        self._assert_dcronjobalert(dcron_job_alerts[0], "command_01", constants.Alert.EXECUTION)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=0, second=5))
    def test_execution_missed_execution_at_schedule(self, mock_now):
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(hours=2),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(hours=2),
            "alert": constants.Alert.EXECUTION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_01", job_kwargs_dict, settings_kwargs_dict)

        dcron_job_alerts = self._get_dcron_job_alerts()
        self.assertEqual(len(dcron_job_alerts), 1)
        self._assert_dcronjobalert(dcron_job_alerts[0], "command_01", constants.Alert.EXECUTION)

    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=0, second=5))
    def test_duration_missed_execution_at_schedule(self, mock_now):
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(hours=3),
            "completed_dt": None,
            "alert": constants.Alert.DURATION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_01", job_kwargs_dict, settings_kwargs_dict)

        dcron_job_alerts = self._get_dcron_job_alerts()
        self.assertEqual(len(dcron_job_alerts), 1)
        self._assert_dcronjobalert(dcron_job_alerts[0], "command_01", constants.Alert.DURATION)


@override_settings(
    DCRON={
        "base_command": "/home/ubuntu/docker-manage-py.sh",
        "check_margin": datetime.timedelta(seconds=5),
        "severities": {},
        "default_warning_wait": 600,
        "warning_waits": {},
        "default_max_duration": 10,
        "max_durations": {},
        "default_min_separation": 30,
        "min_separations": {},
    }
)
class HandleAlertsTestCase(TestCase):
    @mock.patch("utils.pagerduty_helper._post_event")
    @mock.patch("utils.slack.publish")
    @mock.patch("utils.dates_helper.utc_now", return_value=_get_rounded_now(minute=17, second=3))
    def test_many_dcron_jobs(self, mock_now, mock_slack_publish, mock_post_event):
        # Executed in time.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=15),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=14, seconds=57),
            "alert": constants.Alert.OK,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_01", job_kwargs_dict, settings_kwargs_dict)

        # Executed in time, alerting already (alert should not change since it is only updated by  run).
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=15),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=14, seconds=57),
            "alert": constants.Alert.DURATION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_02", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=21),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=20, seconds=57),
            "alert": constants.Alert.OK,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *", "severity": constants.Severity.HIGH}
        _create_job("command_03", job_kwargs_dict, settings_kwargs_dict)

        # Missed last execution, but alerting already.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=21),
            "completed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=20, seconds=57),
            "alert": constants.Alert.EXECUTION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_04", job_kwargs_dict, settings_kwargs_dict)

        # Executed in time, exceeded max_duration.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=15),
            "completed_dt": None,
            "alert": constants.Alert.OK,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *", "ownership": constants.Ownership.PRODOPS}
        _create_job("command_05", job_kwargs_dict, settings_kwargs_dict)

        # Executed in time, exceeded max_duration, but alerting already.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=15),
            "completed_dt": None,
            "alert": constants.Alert.DURATION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_06", job_kwargs_dict, settings_kwargs_dict)

        # Executed in time, exceeded max_duration, but alerting already.
        job_kwargs_dict = {
            "executed_dt": dates_helper.utc_now() - datetime.timedelta(minutes=15),
            "completed_dt": None,
            "alert": constants.Alert.EXECUTION,
        }
        settings_kwargs_dict = {"schedule": "0 * * * *"}
        _create_job("command_07", job_kwargs_dict, settings_kwargs_dict)

        with self.assertNumQueries(5):
            # Two DB queries for initial filters, others for updates.
            alerts.handle_alerts()

        self.assertEqual(models.DCronJob.objects.get(command_name="command_01").alert, constants.Alert.OK)
        self.assertEqual(models.DCronJob.objects.get(command_name="command_02").alert, constants.Alert.DURATION)
        self.assertEqual(models.DCronJob.objects.get(command_name="command_03").alert, constants.Alert.EXECUTION)
        self.assertEqual(models.DCronJob.objects.get(command_name="command_04").alert, constants.Alert.EXECUTION)
        self.assertEqual(models.DCronJob.objects.get(command_name="command_05").alert, constants.Alert.DURATION)
        self.assertEqual(models.DCronJob.objects.get(command_name="command_06").alert, constants.Alert.DURATION)
        self.assertEqual(models.DCronJob.objects.get(command_name="command_06").alert, constants.Alert.DURATION)

        mock_post_event.assert_has_calls(
            [
                mock.call(
                    "trigger",
                    pagerduty_helper.PagerDutyEventType.Z1,
                    "command_03",
                    alerts._alert_message("command_03", constants.Alert.EXECUTION),
                    event_severity=pagerduty_helper.PagerDutyEventSeverity.CRITICAL,
                    details=None,
                ),
                mock.call(
                    "trigger",
                    pagerduty_helper.PagerDutyEventType.Z1,
                    "command_07",
                    alerts._alert_message("command_07", constants.Alert.DURATION),
                    event_severity=pagerduty_helper.PagerDutyEventSeverity.WARNING,
                    details=None,
                ),
            ]
        )

        mock_slack_publish.assert_has_calls(
            [
                mock.call(
                    "",
                    **alerts._create_slack_publish_params(
                        models.DCronJob.objects.get(command_name="command_03"), constants.Alert.EXECUTION
                    )
                ),
                mock.call(
                    "",
                    **alerts._create_slack_publish_params(
                        models.DCronJob.objects.get(command_name="command_05"), constants.Alert.DURATION
                    )
                ),
                mock.call(
                    "",
                    **alerts._create_slack_publish_params(
                        models.DCronJob.objects.get(command_name="command_07"), constants.Alert.DURATION
                    )
                ),
            ]
        )


class SlackAlertTestCase(TestCase):
    @staticmethod
    def generate_params(
        command_name, channel, username, title, title_link, color, fallback, text, field_title, field_value
    ):
        log_viewer_link = settings.DCRON["log_viewer_link"].format(command_name=command_name.replace("_", ""))
        return {
            "channel": channel,
            "msg_type": None,
            "username": username,
            "attachments": [
                {
                    "title": title,
                    "title_link": title_link,
                    "color": color,
                    "fallback": fallback,
                    "text": text,
                    "fields": [
                        {"title": field_title, "value": field_value},
                        {"title": "Log viewer link", "value": log_viewer_link, "short": False},
                    ],
                }
            ],
        }

    def test_create_slack_publish_params_ok_low(self):
        dcron_job = _create_job("some_command", {}, {})

        params = alerts._create_slack_publish_params(dcron_job, constants.Alert.OK)

        self.assertDictEqual(
            params,
            self.generate_params(
                command_name="some_command",
                channel=alerts.SLACK_CHANNEL_Z1_LOW_SEVERITY,
                username=alerts.SLACK_USERNAME,
                title="[OK] Cron Command Alert",
                title_link=settings.BASE_URL + "/admin/dcron/dcronjob/%s/change/" % dcron_job.pk,
                color="good",
                fallback=alerts._alert_message("some_command", constants.Alert.OK),
                text="The problem with a command run by cron has been resolved",
                field_title=dcron_job.command_name,
                field_value=constants.Alert.get_description(constants.Alert.OK),
            ),
        )

    def test_create_slack_publish_params_warning_low(self):
        dcron_job = _create_job("some_command", {}, {})

        params = alerts._create_slack_publish_params(dcron_job, constants.Alert.DURATION)

        self.assertDictEqual(
            params,
            self.generate_params(
                command_name="some_command",
                channel=alerts.SLACK_CHANNEL_Z1_LOW_SEVERITY,
                username=alerts.SLACK_USERNAME,
                title="[Alerting] Cron Command Alert",
                title_link=settings.BASE_URL + "/admin/dcron/dcronjob/%s/change/" % dcron_job.pk,
                color="warning",
                fallback=alerts._alert_message("some_command", constants.Alert.DURATION),
                text="There is a problem with a command run by cron",
                field_title=dcron_job.command_name,
                field_value=constants.Alert.get_description(constants.Alert.DURATION),
            ),
        )

    def test_create_slack_publish_params_danger_low(self):
        dcron_job = _create_job("some_command", {}, {})

        params = alerts._create_slack_publish_params(dcron_job, constants.Alert.FAILURE)

        self.assertDictEqual(
            params,
            self.generate_params(
                command_name="some_command",
                channel=alerts.SLACK_CHANNEL_Z1_LOW_SEVERITY,
                username=alerts.SLACK_USERNAME,
                title="[Alerting] Cron Command Alert",
                title_link=settings.BASE_URL + "/admin/dcron/dcronjob/%s/change/" % dcron_job.pk,
                color="danger",
                fallback=alerts._alert_message("some_command", constants.Alert.FAILURE),
                text="There is a problem with a command run by cron",
                field_title=dcron_job.command_name,
                field_value=constants.Alert.get_description(constants.Alert.FAILURE),
            ),
        )

    def test_create_slack_publish_params_ok_high(self):
        dcron_job = _create_job("some_command", {}, {"severity": constants.Severity.HIGH})

        params = alerts._create_slack_publish_params(dcron_job, constants.Alert.OK)

        self.assertDictEqual(
            params,
            self.generate_params(
                command_name="some_command",
                channel=alerts.SLACK_CHANNEL_Z1_HIGH_SEVERITY,
                username=alerts.SLACK_USERNAME,
                title="[OK] Cron Command Alert",
                title_link=settings.BASE_URL + "/admin/dcron/dcronjob/%s/change/" % dcron_job.pk,
                color="good",
                fallback=alerts._alert_message("some_command", constants.Alert.OK),
                text="The problem with a command run by cron has been resolved",
                field_title=dcron_job.command_name,
                field_value=constants.Alert.get_description(constants.Alert.OK),
            ),
        )

    def test_create_slack_publish_params_warning_high(self):
        dcron_job = _create_job("some_command", {}, {"severity": constants.Severity.HIGH})

        params = alerts._create_slack_publish_params(dcron_job, constants.Alert.DURATION)

        self.assertDictEqual(
            params,
            self.generate_params(
                command_name="some_command",
                channel=alerts.SLACK_CHANNEL_Z1_HIGH_SEVERITY,
                username=alerts.SLACK_USERNAME,
                title="[Alerting] Cron Command Alert",
                title_link=settings.BASE_URL + "/admin/dcron/dcronjob/%s/change/" % dcron_job.pk,
                color="warning",
                fallback=alerts._alert_message("some_command", constants.Alert.DURATION),
                text="There is a problem with a command run by cron",
                field_title=dcron_job.command_name,
                field_value=constants.Alert.get_description(constants.Alert.DURATION),
            ),
        )

    def test_create_slack_publish_params_danger_high(self):
        dcron_job = _create_job("some_command", {}, {"severity": constants.Severity.HIGH})

        params = alerts._create_slack_publish_params(dcron_job, constants.Alert.FAILURE)

        self.assertDictEqual(
            params,
            self.generate_params(
                command_name="some_command",
                channel=alerts.SLACK_CHANNEL_Z1_HIGH_SEVERITY,
                username=alerts.SLACK_USERNAME,
                title="[Alerting] Cron Command Alert",
                title_link=settings.BASE_URL + "/admin/dcron/dcronjob/%s/change/" % dcron_job.pk,
                color="danger",
                fallback=alerts._alert_message("some_command", constants.Alert.FAILURE),
                text="There is a problem with a command run by cron",
                field_title=dcron_job.command_name,
                field_value=constants.Alert.get_description(constants.Alert.FAILURE),
            ),
        )

    def test_create_slack_publish_params_danger_high_prodops(self):
        dcron_job = _create_job(
            "some_command", {}, {"severity": constants.Severity.HIGH, "ownership": constants.Ownership.PRODOPS}
        )

        params = alerts._create_slack_publish_params(dcron_job, constants.Alert.FAILURE)

        self.assertDictEqual(
            params,
            self.generate_params(
                command_name="some_command",
                channel=alerts.SLACK_CHANNEL_PRODOPS_HIGH_SEVERITY,
                username=alerts.SLACK_USERNAME,
                title="[Alerting] Cron Command Alert",
                title_link=settings.BASE_URL + "/admin/dcron/dcronjob/%s/change/" % dcron_job.pk,
                color="danger",
                fallback=alerts._alert_message("some_command", constants.Alert.FAILURE),
                text="There is a problem with a command run by cron",
                field_title=dcron_job.command_name,
                field_value=constants.Alert.get_description(constants.Alert.FAILURE),
            ),
        )
