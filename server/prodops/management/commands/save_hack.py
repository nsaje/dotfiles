import utils.command_helpers
import dash.models

from django.db.models import Q


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
        parser.add_argument('--trello', dest='trelo', default='')

    def _print(self, msg):
        self.stdout.write(u'{}\n'.format(msg))

    def handle(self, *args, **options):
        hack = {}
        if options['source']:
            source = options['sourrce']
            if source == 'b1':
                hack['rtb_only'] = True
            elif source.isdigit():
                hack['source_id'] = int(options['source'])
            else:
                hack['source'] = dash.models.Source.objects.get(
                    Q(bidder_slug='b1_{}'.format(source)) | Q(bidder_slug=source)
                )
        hack['summary'] = options['summary']
        hack['service'] = options['service']
        if options['details']:
            hack['details'] = options['details']
        if options['trello']:
            hack['trello_ticket_url'] = options['trello']
        saved_hacks = 0

        for ad_group in filter(bool, options.get('ad_groups', '').split(',')):
            dash.models.CustomHack.objects.create(ad_group_id=int(ad_group), **hack)
            saved_hacks += 1
        for campaign in filter(bool, options.get('campaigns', '').split(',')):
            dash.models.CustomHack.objects.create(campaign_id=int(campaign), **hack)
            saved_hacks += 1
        for account in filter(bool, options.get('accounts', '').split(',')):
            dash.models.CustomHack.objects.create(account_id=int(account), **hack)
            saved_hacks += 1
        for agency in filter(bool, options.get('agencies', '').split(',')):
            dash.models.CustomHack.objects.create(agency_id=int(agency), **hack)
            saved_hacks += 1

        print 'Saved hacks', saved_hacks
