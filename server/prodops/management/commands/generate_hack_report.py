import datetime
from decimal import Decimal
from collections import Counter

import utils.command_helpers
import dash.models
import redshiftapi.db

from django.db.models import Count, Min

RS_QUERY = '''SELECT {entity}_id, (NVL(SUM(effective_cost_nano), 0) / 1000000000.0 / {n})::decimal
FROM mv_master
WHERE date >= '{start_date}' AND date <= '{end_date}'
GROUP BY {entity}_id'''


class Command(utils.command_helpers.ExceptionCommand):
    help = "Hack report"

    def add_arguments(self, parser):
        parser.add_argument('date', type=str, nargs='?')
        parser.add_argument('--ignore', type=str, dest='ignore', default='',
                            help='Ignore specific hack summary (semicolon separated)')
        parser.add_argument('-n', type=int, dest='n', default=7, help='Number of days')

    def handle(self, *args, **options):
        self.buff = ''

        n = options['n']
        today = datetime.date.today()
        if options['date']:
            today = datetime.datetime.strptime(options['date'], '%Y-%m-%d').date()
        ignore = (options['ignore']).split(';')
        n_days_before = today - datetime.timedelta(n - 1)

        spend_data = self._get_spend_data(n_days_before, today)

        hacks_per_summary = self._get_hacks_per_summary(today)

        stats_by_implemented = dash.models.CustomHack.objects.filter(
            removed_dt__isnull=True,
            created_dt__lt=today + datetime.timedelta(1),
        ).values('summary', 'service').annotate(
            Count("id"), Min('created_dt')
        ).order_by('-id__count')

        stats_by_created = dash.models.CustomHack.objects.filter(
            removed_dt__isnull=True,
            created_dt__gte=n_days_before,
            created_dt__lt=today + datetime.timedelta(1)
        ).values('summary', 'service').annotate(
            Count("id")
        ).order_by('-id__count')

        stats_by_removed = dash.models.CustomHack.objects.filter(
            removed_dt__isnull=False,
            removed_dt__gte=n_days_before,
            created_dt__lt=today + datetime.timedelta(1)
        ).values('summary', 'service').annotate(
            Count("id")
        ).order_by('-id__count')

        stats_by_client = self._get_stats_by_client(today)

        self._print('')
        self._print('***********************************************')
        self._print('********** HACK REPORT on {} **********'.format(today))
        self._print('***********************************************')
        self._print('')

        self._print('New hacks in last {} days:'.format(n))
        for stats in stats_by_created:
            if stats['summary'] in ignore:
                continue
            self._print(' - {} ({}): {}'.format(stats['summary'], stats['service'], stats['id__count']))
        self._print('')

        self._print('New hack implementations in last {} days:'.format(n))
        for stats in stats_by_implemented:
            if stats['summary'] in ignore:
                continue
            if stats['created_dt__min'].date() < n_days_before:
                continue
            self._print(' - {} ({}): on {}'.format(stats['summary'], stats['service'], stats['created_dt__min'].date()))
        self._print('')

        self._print('Removed hacks in last {} days:'.format(n))
        for stats in stats_by_removed:
            if stats['summary'] in ignore:
                continue
            self._print(' - {} ({}): {}'.format(stats['summary'], stats['service'], stats['id__count']))
        self._print('')

        self._print('Most hacked ad groups:')
        for ad_group, cnt in stats_by_client['ad_group'].most_common(3):
            media = spend_data['ad_group'].get(ad_group.pk, Decimal(0))
            self._print(' - #{} {}, Ad Group {}: {} ({}, {})'.format(
                ad_group.pk,
                ad_group.campaign.get_long_name(),
                ad_group.name,
                cnt,
                self._sph(media, cnt),
                self._spd(media)
            ))
        self._print('')

        self._print('Most hacked campaigns:')
        for campaign, cnt in stats_by_client['campaign'].most_common(3):
            media = spend_data['campaign'].get(campaign.pk, Decimal(0))
            self._print(' - #{} {}: {} ({}, {})'.format(
                campaign.pk,
                campaign.get_long_name(),
                cnt,
                self._sph(media, cnt),
                self._spd(media),
            ))
        self._print('')

        self._print('Most hacked accounts:')
        for account, cnt in stats_by_client['account'].most_common(3):
            media = spend_data['account'].get(account.pk, Decimal(0))
            self._print(' - #{} {}: {} ({}, {})'.format(
                account.pk,
                account.get_long_name(),
                cnt,
                self._sph(media, cnt),
                self._spd(media)
            ))
        self._print('')

        self._print('Most hacked agencies:')
        for agency, cnt in stats_by_client['agency'].most_common(3):
            media = spend_data['agency'].get(agency.pk, Decimal(0))
            self._print(' - #{} {}: {} ({}, {})'.format(
                agency.pk,
                agency.name,
                cnt,
                self._sph(media, cnt),
                self._spd(media),
            ))
        self._print('')

        self._print('Total hacks:')
        for stats in stats_by_implemented:
            hacks = hacks_per_summary.get(stats['summary'], [])
            media = self._calc_media_from_hacks(spend_data, hacks)
            self._print(' - {} ({}): {} ({}, {})'.format(
                stats['summary'],
                stats['service'],
                stats['id__count'],
                self._sph(media, len(hacks)),
                self._spd(media),
            ))
        self._print('')

        self._print(
            'Note 1: \'Most hacked\' is calculated as total number of hacks '
            'per current level and all lower levels. For example ad group level report includes '
            'only ad group level hacks, but agency level report includes '
            'all hacks on agency, account, campaign, and ad group level.'
        )
        self._print(
            'Note 2: SpD = (Media) Spend per Day. Spend is calculated for the last {} days.'.format(n) +
            'SpD tells you how much data can you potentially loose each day'
        )
        self._print(
            'Note 3: SpH = SpH = SpD / # of hacks. SpH tells you how much a hack is worth per day'.format(n)
        )

    def _print(self, msg):
        line = u'{}\n'.format(msg)
        self.stdout.write(line)
        self.buff += line

    def _calc_media_from_hacks(self, spend_data, hacks):
        media = Decimal(0)
        for hack in hacks:
            if hack.ad_group_id:
                media += spend_data['ad_group'].get(hack.ad_group_id, Decimal(0))
            elif hack.campaign_id:
                media += spend_data['campaign'].get(hack.campaign_id, Decimal(0))
            elif hack.account_id:
                media += spend_data['account'].get(hack.account_id, Decimal(0))
            elif hack.agency_id:
                media += spend_data['agency'].get(hack.agency_id, Decimal(0))
        return media

    def _sph(self, media, hacks_num):
        sph = Decimal(0)
        if media and hacks_num:
            sph = (media / Decimal(hacks_num)).quantize(Decimal('.01'))
        return 'SpH ${}'.format(sph)

    def _spd(self, media):
        return 'SpD ${}'.format((media or Decimal(0)).quantize(Decimal('.01')))

    def _get_spend_data(self, start_date, end_date):
        spend_data = {}
        with redshiftapi.db.get_stats_cursor() as cur:
            for entity in ['ad_group', 'campaign', 'account', 'agency']:
                cur.execute(RS_QUERY.format(entity=entity,
                                            start_date=str(start_date),
                                            end_date=str(end_date),
                                            n=(end_date - start_date).days + 1))
                spend_data[entity] = {row[0]: row[1] for row in cur.fetchall()}
        return spend_data

    def _get_hacks_per_summary(self, today):
        hacks_per_summary = {}
        for hack in dash.models.CustomHack.objects.filter(
                removed_dt__isnull=True,
                created_dt__lt=today + datetime.timedelta(1)):
            hacks_per_summary.setdefault(hack.summary, []).append(hack)
        return hacks_per_summary

    def _get_stats_by_client(self, today):
        hacks_by_ad_group = {}
        hacks_by_campaign = {}
        hacks_by_account = {}
        hacks_by_agency = {}
        active_hacks = dash.models.CustomHack.objects.filter(
            removed_dt__isnull=True,
            created_dt__lt=today + datetime.timedelta(1)
        ).select_related(
            'ad_group__campaign__account__agency',
            'campaign__account__agency',
            'account__agency',
            'agency'
        )
        for hack in active_hacks:
            if hack.ad_group:
                hacks_by_ad_group.setdefault(hack.ad_group, []).append(hack)
                hacks_by_campaign.setdefault(hack.ad_group.campaign, []).append(hack)
                hacks_by_account.setdefault(hack.ad_group.campaign.account, []).append(hack)
                if hack.ad_group.campaign.account.agency:
                    hacks_by_agency.setdefault(hack.ad_group.campaign.account.agency, []).append(hack)
            if hack.campaign:
                hacks_by_campaign.setdefault(hack.campaign, []).append(hack)
                hacks_by_account.setdefault(hack.campaign.account, []).append(hack)
                if hack.campaign.account.agency:
                    hacks_by_agency.setdefault(hack.campaign.account.agency, []).append(hack)
            if hack.account:
                hacks_by_account.setdefault(hack.account, []).append(hack)
                if hack.account.agency:
                    hacks_by_agency.setdefault(hack.account.agency, []).append(hack)
            if hack.agency:
                hacks_by_agency.setdefault(hack.agency, []).append(hack)
        return {
            'ad_group': Counter({entity: len(hacks) for entity, hacks in hacks_by_ad_group.iteritems()}),
            'campaign': Counter({entity: len(hacks) for entity, hacks in hacks_by_campaign.iteritems()}),
            'account': Counter({entity: len(hacks) for entity, hacks in hacks_by_account.iteritems()}),
            'agency': Counter({entity: len(hacks) for entity, hacks in hacks_by_agency.iteritems()}),
        }
