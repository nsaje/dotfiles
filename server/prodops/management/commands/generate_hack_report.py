import datetime
from decimal import Decimal
from collections import Counter

import utils.command_helpers
import dash.models
import redshiftapi.db

import influx
from django.db.models import Count, Min

RS_QUERY = '''SELECT {entity}_id, (COALESCE(SUM(effective_cost_nano), 0) / 1000000000.0 / {n})::decimal
FROM mv_master
WHERE date >= '{start_date}' AND date <= '{end_date}'
GROUP BY {entity}_id'''


class Command(utils.command_helpers.ExceptionCommand):
    help = "Hack report"

    def add_arguments(self, parser):
        parser.add_argument('date', type=str, nargs='?')
        parser.add_argument('--ignore', type=str, dest='ignore', default='',
                            help='Ignore specific hack summary (semicolon separated) for new/removed metrics')
        parser.add_argument('-n', type=int, dest='n', default=7, help='Number of days')
        parser.add_argument('-i', '--influx', action='store_true', dest='influx', help='Post to Influx')

    def handle(self, *args, **options):
        self.buff = ''

        self.n = options['n']
        self.today = datetime.date.today()
        if options['date']:
            self.today = datetime.datetime.strptime(options['date'], '%Y-%m-%d').date()
        self.ignore = (options['ignore']).split(';')
        self.n_days_before = self.today - datetime.timedelta(self.n - 1)

        self.spend_data = self._get_spend_data(self.n_days_before, self.today)

        self.hacks_per_summary = self._get_hacks_per_summary(self.today)

        self.stats_by_implemented = dash.models.CustomHack.objects.filter(
            removed_dt__isnull=True,
            created_dt__lt=self.today + datetime.timedelta(1),
        ).values('summary', 'service').annotate(
            Count("id"), Min('created_dt')
        ).order_by('-id__count')

        self.stats_by_created = dash.models.CustomHack.objects.filter(
            removed_dt__isnull=True,
            created_dt__gte=self.n_days_before,
            created_dt__lt=self.today + datetime.timedelta(1)
        ).values('summary', 'service').annotate(
            Count("id")
        ).order_by('-id__count')

        self.stats_by_removed = dash.models.CustomHack.objects.filter(
            removed_dt__isnull=False,
            removed_dt__gte=self.n_days_before,
            created_dt__lt=self.today + datetime.timedelta(1)
        ).values('summary', 'service').annotate(
            Count("id")
        ).order_by('-id__count')

        self.stats_by_client = self._get_stats_by_client()
        self.stats_by_source = self._get_stats_by_source()

        if options.get('influx'):
            self.post_to_influx()
        else:
            self.print_report()

    def print_report(self):
        self._print('')
        self._print('***********************************************')
        self._print('********** HACK REPORT on {} **********'.format(self.today))
        self._print('***********************************************')
        self._print('')

        self._print('New hacks in last {} days:'.format(self.n))
        for stats in self.stats_by_created:
            if stats['summary'] in self.ignore:
                continue
            self._print(' - {} ({}): {}'.format(stats['summary'], stats['service'], stats['id__count']))
        self._print('')

        self._print('New hack implementations in last {} days:'.format(self.n))
        for stats in self.stats_by_implemented:
            if stats['summary'] in self.ignore:
                continue
            if stats['created_dt__min'].date() < self.n_days_before:
                continue
            self._print(' - {} ({}): on {}'.format(stats['summary'], stats['service'], stats['created_dt__min'].date()))
        self._print('')

        self._print('Removed hacks in last {} days:'.format(self.n))
        for stats in self.stats_by_removed:
            if stats['summary'] in self.ignore:
                continue
            self._print(' - {} ({}): {}'.format(stats['summary'], stats['service'], stats['id__count']))
        self._print('')

        self._print('Most hacked ad groups:')
        for ad_group, cnt in self.stats_by_client['ad_group'].most_common(3):
            media = self.spend_data['ad_group'].get(ad_group.pk, Decimal(0))
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
        for campaign, cnt in self.stats_by_client['campaign'].most_common(3):
            media = self.spend_data['campaign'].get(campaign.pk, Decimal(0))
            self._print(' - #{} {}: {} ({}, {})'.format(
                campaign.pk,
                campaign.get_long_name(),
                cnt,
                self._sph(media, cnt),
                self._spd(media),
            ))
        self._print('')

        self._print('Most hacked accounts:')
        for account, cnt in self.stats_by_client['account'].most_common(3):
            media = self.spend_data['account'].get(account.pk, Decimal(0))
            self._print(' - #{} {}: {} ({}, {})'.format(
                account.pk,
                account.get_long_name(),
                cnt,
                self._sph(media, cnt),
                self._spd(media)
            ))
        self._print('')

        self._print('Most hacked agencies:')
        for agency, cnt in self.stats_by_client['agency'].most_common(3):
            media = self.spend_data['agency'].get(agency.pk, Decimal(0))
            self._print(' - #{} {}: {} ({}, {})'.format(
                agency.pk,
                agency.name,
                cnt,
                self._sph(media, cnt),
                self._spd(media),
            ))
        self._print('')

        self._print('Most hacked sources:')
        for source, cnt in Counter(self.stats_by_source).most_common(5):
            self._print(' - {}: {}'.format(
                source,
                cnt
            ))
        self._print('')

        self._print('Total hacks:')
        for stats in self.stats_by_implemented:
            hacks = self.hacks_per_summary.get(stats['summary'], [])
            media = self._calc_media_from_hacks(self.spend_data, hacks)
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
            'Note 2: SpD = (Media) Spend per Day. Spend is calculated for the last {} days.'.format(self.n) +
            'SpD tells you how much data can you potentially loose each day'
        )
        self._print(
            'Note 3: SpH = SpD / # of hacks. SpH tells you how much a hack is worth per day'.format(self.n)
        )

    def post_to_influx(self):
        for stats in self.stats_by_removed:
            if stats['summary'] in self.ignore:
                continue
            influx.gauge('backendhack_status_count', stats['id__count'],
                         status='removed', summary=stats['summary'], retentionPolicy='1week')
        for stats in self.stats_by_implemented:
            if stats['summary'] in self.ignore:
                continue
            if stats['created_dt__min'].date() < self.n_days_before:
                influx.gauge('backendhack_status_count', stats['id__count'],
                             status='existing', summary=stats['summary'], retentionPolicy='1week')
            else:
                influx.gauge('backendhack_status_count', stats['id__count'],
                             status='fresh', summary=stats['summary'], retentionPolicy='1week')

        for stats in self.stats_by_implemented:
            hacks = self.hacks_per_summary.get(stats['summary'], [])
            media = self._calc_media_from_hacks(self.spend_data, hacks)
            influx.gauge('backendhack_service_spd', media,
                         summary=stats['summary'], service=stats['service'], retentionPolicy='1week')
            influx.gauge('backendhack_service_count', stats['id__count'],
                         summary=stats['summary'], service=stats['service'], retentionPolicy='1week')

        for account, cnt in self.stats_by_client['account'].most_common(10):
            media = self.spend_data['account'].get(account.pk, Decimal(0))
            influx.gauge('backendhack_account_spd', media,
                         client=account.name, retentionPolicy='1week')
            influx.gauge('backendhack_account_count', cnt,
                         client=account.name, retentionPolicy='1week')

        for agency, cnt in self.stats_by_client['agency'].most_common(10):
            media = self.spend_data['agency'].get(agency.pk, Decimal(0))
            influx.gauge('backendhack_agency_spd', media,
                         client=agency.name, retentionPolicy='1week')
            influx.gauge('backendhack_agency_count', cnt,
                         client=agency.name, retentionPolicy='1week')

        for source, cnt in self.stats_by_source.items():
            influx.gauge('backendhack_source_count', cnt,
                         source=source, retentionPolicy='1week')

    def _print(self, msg):
        line = '{}\n'.format(msg)
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
            for entity in ['ad_group', 'campaign', 'account']:
                cur.execute(RS_QUERY.format(entity=entity,
                                            start_date=str(start_date),
                                            end_date=str(end_date),
                                            n=(end_date - start_date).days + 1))
                spend_data[entity] = {row[0]: row[1] for row in cur.fetchall()}
        spend_data['agency'] = {a.pk: Decimal(0) for a in dash.models.Agency.objects.all()}
        for acc in dash.models.Account.objects.filter(agency_id__isnull=False):
            spend_data['agency'][acc.agency_id] += spend_data['account'].get(acc.pk, Decimal(0))
        return spend_data

    def _get_hacks_per_summary(self, today):
        hacks_per_summary = {}
        for hack in dash.models.CustomHack.objects.filter(
                removed_dt__isnull=True,
                created_dt__lt=today + datetime.timedelta(1)):
            hacks_per_summary.setdefault(hack.summary, []).append(hack)
        return hacks_per_summary

    def _get_stats_by_source(self):
        stats = {}
        active_hacks = dash.models.CustomHack.objects.filter(
            removed_dt__isnull=True,
            created_dt__lt=self.today + datetime.timedelta(1)
        ).select_related('source')
        for hack in active_hacks:
            if hack.source is None:
                if hack.rtb_only:
                    stats.setdefault('rtb', []).append(hack)
                else:
                    stats.setdefault('all', []).append(hack)
            else:
                stats.setdefault(hack.source.name, []).append(hack)
        return {source: len(hacks) for source, hacks in stats.items()}

    def _get_stats_by_client(self):
        hacks_by_ad_group = {}
        hacks_by_campaign = {}
        hacks_by_account = {}
        hacks_by_agency = {}
        active_hacks = dash.models.CustomHack.objects.filter(
            removed_dt__isnull=True,
            created_dt__lt=self.today + datetime.timedelta(1)
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
            'ad_group': Counter({entity: len(hacks) for entity, hacks in hacks_by_ad_group.items()}),
            'campaign': Counter({entity: len(hacks) for entity, hacks in hacks_by_campaign.items()}),
            'account': Counter({entity: len(hacks) for entity, hacks in hacks_by_account.items()}),
            'agency': Counter({entity: len(hacks) for entity, hacks in hacks_by_agency.items()}),
        }
