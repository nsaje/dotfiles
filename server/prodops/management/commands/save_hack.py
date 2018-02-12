import utils.command_helpers
import dash.models

from django.db.models import Q

LOOKUP_KEYS = ('service', 'summary', 'source', 'source_id', 'rtb_only', )


class Command(utils.command_helpers.ExceptionCommand):
    help = "Store hack"

    def add_arguments(self, parser):
        parser.add_argument('service', type=str)
        parser.add_argument('summary', type=str)
        parser.add_argument('--ad-groups', dest='ad_groups', default='')
        parser.add_argument('--campaigns', dest='campaigns', default='')
        parser.add_argument('--accounts', dest='accounts', default='')
        parser.add_argument('--agencies', dest='agencies', default='')
        parser.add_argument('--source', dest='source', default='b1')
        parser.add_argument('--details', dest='details', default='')
        parser.add_argument('--trello', dest='trello', default='')
        parser.add_argument(
            '--clear', dest='clear',
            default=False, action='store_true',
            help='Clear all previous hacks with the same summary'
        )

    def _print(self, msg):
        self.stdout.write('{}\n'.format(msg))

    def _confirm(self, message):
        return input('{} [yN] '.format(message)).lower() == 'y'

    def handle(self, *args, **options):
        hack, lookup = {}, {}
        source = options['source']

        hack['rtb_only'] = False
        if source == 'b1':
            hack['rtb_only'] = True
        elif source.isdigit():
            hack['source_id'] = int(source)
        elif source:
            hack['source'] = dash.models.Source.objects.get(
                Q(bidder_slug='b1_{}'.format(source)) | Q(bidder_slug=source)
            )
        hack['summary'] = options['summary']
        hack['service'] = options['service']
        hack['removed_dt'] = None
        hack['confirmed_dt'] = None
        hack['confirmed_by'] = None
        if options['details']:
            hack['details'] = options['details']
        if options['trello']:
            hack['trello_ticket_url'] = options['trello']

        lookup = {key: hack[key] for key in LOOKUP_KEYS if key in hack}

        if options['clear'] and self._confirm('Are you sure you want to delete related hacks with summary "{}"'.format(hack['summary'])):
            dash.models.CustomHack.objects.filter(**lookup).delete()

        new_hacks, updated_hacks = 0, 0

        for ad_group in filter(bool, options.get('ad_groups', '').split(',')):
            _, created = dash.models.CustomHack.objects.update_or_create(
                defaults=hack, ad_group_id=int(ad_group), **lookup)
            new_hacks += (1 if created else 0)
            updated_hacks += (1 if not created else 0)
        for campaign in filter(bool, options.get('campaigns', '').split(',')):
            _, created = dash.models.CustomHack.objects.update_or_create(
                defaults=hack, campaign_id=int(campaign), **lookup)
            new_hacks += (1 if created else 0)
            updated_hacks += (1 if not created else 0)
        for account in filter(bool, options.get('accounts', '').split(',')):
            _, created = dash.models.CustomHack.objects.update_or_create(
                defaults=hack, account_id=int(account), **lookup)
            new_hacks += (1 if created else 0)
            updated_hacks += (1 if not created else 0)
        for agency in filter(bool, options.get('agencies', '').split(',')):
            _, created = dash.models.CustomHack.objects.update_or_create(defaults=hack, agency_id=int(agency), **lookup)
            new_hacks += (1 if created else 0)
            updated_hacks += (1 if not created else 0)

        print('New hacks', new_hacks)
        print('Updated hacks', updated_hacks)
