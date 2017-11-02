import logging
import influx
import datetime
import gzip
from StringIO import StringIO

from dash import models
from utils.command_helpers import ExceptionCommand
from utils import s3helpers, email_helper, dates_helper, csv_utils
from stats.api_breakdowns import Goals
import redshiftapi.api_breakdowns

logger = logging.getLogger(__name__)

S3_BUCKET_B1_ML = 'b1-ml'
S3_CPA_FACTORS_PATH = 'postclick_kpi/siciliana/actionspercost/trim_ratios/agsrcpub/latest/trimratios.tsv.gz'
OEN_ACCOUNT = 305
OEN_PUBLISHER_GROUP_ID = 2
DATA_LOOK_BACK_DAYS = 14
EXPECTED_COLS = ['adgroup', 'action', 'source', 'publisher', 'ob_pub_id', 'campaign',
                 'ob_campaign', 'media_spend', 'conversions', 'factor']


class Command(ExceptionCommand):

    help = "Sends Post-click KPI Optimization CPA factors in email to OEN"

    @influx.timer('dash.commands.send_oen_postclickkpi_cpa_email_job.running_time')
    def handle(self, *args, **options):
        logger.info('Sending OEN post click kpi optimization CPA factors email')

        sources = {s.get_clean_slug(): s for s in models.Source.objects.all()}
        oen_ags = models.AdGroup.objects.filter(campaign__account=OEN_ACCOUNT).select_related('campaign')
        oen_pub_ids = self._prefetch_oen_pub_ids()

        s3_helper = s3helpers.S3Helper(S3_BUCKET_B1_ML)
        factors_file = gzip.GzipFile(fileobj=StringIO(s3_helper.get(S3_CPA_FACTORS_PATH))).read()

        factors_ad_groups = self._get_factor_ad_groups(factors_file, oen_ags)
        conversions_data = self._get_conversions_data(factors_ad_groups)
        factors = self._generate_output_csv(factors_file, oen_ags, sources, conversions_data, oen_pub_ids)

        email_helper.send_oen_postclickkpi_cpa_factors_email(factors)
        influx.gauge('dash.commands.send_oen_postclickkpi_cpa_email_job.num_factors', len(factors.splitlines()))

    def _generate_output_csv(self, factors_file, ad_groups, sources, conversions_data, oen_pub_ids):
        rows = self._generate_output_csv_rows(factors_file, ad_groups, sources, conversions_data, oen_pub_ids)
        return csv_utils.tuplelist_to_csv(rows)

    def _generate_output_csv_rows(self, factors_file, ad_groups, sources, conversions_data, oen_pub_ids):
        yield EXPECTED_COLS

        for factor_row in factors_file.splitlines():
            row = factor_row.split('\t')

            out, adg = self._parse_row(row, ad_groups)
            if not adg:
                continue

            out['campaign'] = adg.campaign.id
            out['ob_campaign'] = adg.campaign.name

            out['factor'] = row[2]

            pub_key = ','.join([out['publisher'], str(sources[out['source']].id)])
            oen_ids = oen_pub_ids[pub_key] if pub_key in oen_pub_ids else []
            out['ob_pub_id'] = '-'.join(oen_ids)

            key = ','.join([str(out['adgroup']), str(sources[out['source']].id), out['publisher']])
            current_data = conversions_data.get(key, {})
            out['media_spend'] = current_data.get('media_spend', '')
            out['conversions'] = current_data.get('conversions', '')

            for col in EXPECTED_COLS:
                if col not in out:
                    raise Exception('Unexpected factor key in factor row: %s' % factor_row)

            yield [out[c] for c in EXPECTED_COLS]

    def _get_conversions_data(self, ad_group_ids):
        data = redshiftapi.api_breakdowns.query_all(
            ['ad_group_id', 'source_id', 'publisher'],
            {
                'date__lte': dates_helper.local_today(),
                'date__gte': dates_helper.local_today() - datetime.timedelta(days=DATA_LOOK_BACK_DAYS),
                'ad_group_id': ad_group_ids,
            },
            parents=None,
            goals=Goals(
                campaign_goals=None,
                conversion_goals=None,
                campaign_goal_values=None,
                pixels=[models.ConversionPixel.objects.get(id=844)],
                primary_goals=None, ),
            use_publishers_view=True,
        )

        conversions_data = {}
        for d in data:
            pub = d['publisher'][4:] if d['publisher'].startswith('www.') else d['publisher']
            key = ','.join([str(d['ad_group_id']), str(d['source_id']), pub])
            if key in conversions_data:
                conversions_data[key]['conversions'] += d.get('pixel_844_2160', 0) or 0
                conversions_data[key]['media_spend'] += float(d.get('media_cost', 0.0) or 0.0)
            else:
                conversions_data[key] = {
                    'conversions': d.get('pixel_844_2160', 0) or 0,
                    'media_spend': float(d.get('media_cost', 0.0) or 0.0),
                }

        return conversions_data

    def _get_factor_ad_groups(self, factors_file, oen_ad_groups):
        adg_ids = []
        for factor_row in factors_file.splitlines():
            out, adg = self._parse_row(factor_row.split('\t'), oen_ad_groups)
            if adg:
                adg_ids.append(adg.id)
        return adg_ids

    def _parse_row(self, row, ad_groups):
        out = {}

        if len(row) != 3:
            raise Exception('Expected 3 parts in factor row: %s' % row)

        for part in row[1].split(';'):
            s = part.split('=')
            if len(s) != 2:
                raise Exception('Expected 2 parts in factor key in row: %s' % row)
            out[s[0]] = s[1]

        try:
            adg = ad_groups.get(id=out['adgroup'])
        except models.AdGroup.DoesNotExist:
            adg = None

        return out, adg

    def _prefetch_oen_pub_ids(self):
        oen_pub_ids = {}
        for pge in models.PublisherGroup.objects.get(pk=OEN_PUBLISHER_GROUP_ID).entries.all():
            pub = (pge.publisher[4:] if pge.publisher.startswith('www.') else pge.publisher).strip()
            if not pge.source:
                continue
            key = ','.join([pub, str(pge.source.id)])
            if key in oen_pub_ids:
                oen_pub_ids[key].append(pge.outbrain_publisher_id)
            else:
                oen_pub_ids[key] = [pge.outbrain_publisher_id]
        return oen_pub_ids
