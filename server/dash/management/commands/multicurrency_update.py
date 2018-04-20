from utils.command_helpers import ExceptionCommand

import core.multicurrency
import dash.constants


class Command(ExceptionCommand):

    help = 'Updates currency exchange rates'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--currency', type=str, choices=dash.constants.Currency.get_all())

    def handle(self, *args, **options):
        kwargs = {}
        if options['currency']:
            kwargs['currencies'] = [options['currency']]
        core.multicurrency.update_exchange_rates(**kwargs)
