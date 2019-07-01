import influx

import core.features.multicurrency
import dash.constants
from utils.command_helpers import Z1Command


class Command(Z1Command):

    help = "Updates currency exchange rates"

    def add_arguments(self, parser):
        parser.add_argument("-c", "--currency", type=str, choices=dash.constants.Currency.get_all())

    @influx.timer("multicurrency.job_run")
    def handle(self, *args, **options):
        kwargs = {}
        if options["currency"]:
            kwargs["currencies"] = [options["currency"]]
        core.features.multicurrency.update_exchange_rates(**kwargs)
