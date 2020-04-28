# Introduction

The `dcron` app makes it possible to run cron jobs in a distributed way since it provides the neccessary locking to prevent concurrent executions of jobs of the same type on different machines.

In addition it provides a standardised reporting and alerting for all jobs run by cron that are described in `crontab.txt` file.

See [Z1 Cron Jobs](https://grafana.zemanta.com/d/G6-o80Bmk/z1-cron-jobs) Grafana dashboard for job execution reports.

# Models

There are two models provided by `dcron` app. The `DCronJob` stores basic information about the last job execution and related alerts. The `DCronJobSettings` model stores per job configuration as is read from `crontab.txt` file and from `settings.DCRON` configuration.

## Synchronization with `crontab.txt` file

The `DCronJobSettings` values are populated by `sync_dcron_jobs` management command at the end of each deploy. It reads the `crontab.txt` file and creates, updates or deletes `DCronJobSettings` records to match the contents of the file.

## `DCronJobSettings`

The following fields are read from `crontab.txt` file and should not be updated manually and are thus read-only in the admin (so that they remain consistent with crontab on servers):

* `schedule`
* `full_command`
* `enabled`

The following fields are populated from `settings.DCRON` configuration:

* `severity`
* `ownership`
* `warning_wait`
* `max_duration`
* `min_separation`

For each of these fields `settings.DCRON` can provide override values for specified jobs, If there is no override value, the default value is used for each of these fields as specified by `settings.DCRON`. These values control the alerting and execution for configured cron jobs.

The `check_dcron_jobs` management command periodically checks the execution data for each job and in case of problems with job execution triggers alerts to pagerduty and Slack.

### `severity`

This configuration value describes the alerting severity of a job. Possible values are:

* `dcron.constants.Severity.LOW`
* `dcron.constants.Severity.HIGH`

The default value is `LOW`, which means that pagerduty alert is non-critical  and that Slack messages are sent to "z1-team-alerts-aux" channel. For `HIGH` severity jobs the alerts in pagerduty are critical and Slack messages are sent to "z1-team-alerts" channel.

### `ownership`

This configuration value describes the alerting ownership of a job. Possible values are:

* `dcron.constants.Ownership.Z1`
* `dcron.constants.Ownership.PRODOPS`

The default value is `Z1`, which means that pagerduty alert is sent to Z1 team. For `PRODOPS` the alerts in pagerduty are sent to ProdOps team.

### `warning_wait`

This configuration value describes how long to wait before triggering a warning alert if job execution is late. The value is specified in seconds.

### `max_duration`

This configuration value describes the maximum duration of a job in seconds before triggering an alert.

### `min_separation`

This configuration value is not related to alerting. It is used to prevent the same job to be executed on different machines due to a short job run time and a time difference or a difference in job start up time on different machines.

### Manual override

There is an additional field `manual_override` which in case it is set to `True` prevents the values that are configured for a certain job (for example the values provided through the admin interface) to be updated by `sync_dcron_jobs` command. It makes it possible to preserve manual configuration values across deploys.
