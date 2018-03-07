import influx

import automation.campaignstop

from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):

    @influx.timer('campaignstop.job_run', job='handle_updates')
    def handle(self, *args, **options):
        automation.campaignstop.handle_updates()
