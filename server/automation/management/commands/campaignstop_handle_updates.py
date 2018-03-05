import influx

import automation.campaignstop

from utils.command_helpers import ExceptionCommand


class Command(ExceptionCommand):

    @influx.timer('campaignstop.handle_updates_job')
    def handle(self, *args, **options):
        automation.campaignstop.handle_updates()
