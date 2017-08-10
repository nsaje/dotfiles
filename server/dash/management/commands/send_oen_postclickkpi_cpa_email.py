import logging
import cStringIO
import influx
import unicodecsv
import datetime

from dash import models
from utils.command_helpers import ExceptionCommand
from utils import s3helpers, email_helper, dates_helper
from stats.api_breakdowns import Goals
import redshiftapi.api_breakdowns

logger = logging.getLogger(__name__)

S3_BUCKET_B1_ML = 'b1-ml'
S3_CPA_FACTORS_PATH = 'postclick_kpi/siciliana/actionspercost/trim_ratios/agsrcpub/latest/trimratios.tsv'
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
        oen_pub_group = models.PublisherGroup.objects.get(pk=OEN_PUBLISHER_GROUP_ID)
        conversions_data = self._get_conversions_data([adg.id for adg in oen_ags])

        factors = self._generate_output_csv(oen_ags, sources, conversions_data, oen_pub_group)

        email_helper.send_oen_postclickkpi_cpa_factors_email(factors)
        influx.gauge('dash.commands.send_oen_postclickkpi_cpa_email_job.num_factors', len(factors.splitlines()))

    def _generate_output_csv(self, ad_groups, sources, conversions_data, oen_pub_group):

        output = cStringIO.StringIO()
        writer = unicodecsv.writer(output, encoding='utf-8', delimiter=';')
        writer.writerow(EXPECTED_COLS)

        s3_helper = s3helpers.S3Helper(S3_BUCKET_B1_ML)
        f = s3_helper.get(S3_CPA_FACTORS_PATH)

        for factor_row in f.splitlines():
            row = factor_row.split('\t')
            out = {}

            if len(row) != 3:
                raise Exception('Expected 3 parts in factor row: %s' % factor_row)

            for part in row[1].split(';'):
                s = part.split('=')
                if len(s) != 2:
                    raise Exception('Expected 2 parts in factor key in row: %s' % factor_row)
                out[s[0]] = s[1]

            try:
                adg = ad_groups.get(id=out['adgroup'])
            except models.AdGroup.DoesNotExist:
                continue
            out['campaign'] = adg.campaign.id
            out['ob_campaign'] = adg.campaign.name

            out['factor'] = row[2]

            oen_pubs = oen_pub_group.entries.filter(publisher__in=[out['publisher'], 'www.' + out['publisher']],
                                                    source=sources[out['source']])
            out['ob_pub_id'] = ','.join(set([p.outbrain_publisher_id for p in oen_pubs]))

            key = ','.join([str(out['adgroup']), str(sources[out['source']].id), out['publisher']])
            current_data = conversions_data.get(key, {})
            out['media_spend'] = current_data.get('media_spend', '')
            out['conversions'] = current_data.get('conversions', '')

            for col in EXPECTED_COLS:
                if col not in out:
                    raise Exception('Unexpected factor key in factor row: %s' % factor_row)

            writer.writerow([out[c] for c in EXPECTED_COLS])

        return output.getvalue()

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
                conversions_data[key]['media_spend'] += d.get('media_cost', 0.0) or 0.0
            else:
                conversions_data[key] = {
                    'conversions': d.get('pixel_844_2160', 0) or 0,
                    'media_spend': d.get('media_cost', 0.0) or 0.0,
                }

        return conversions_data