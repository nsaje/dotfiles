import logging
import cStringIO
import influx
import unicodecsv

from dash import models
from utils.command_helpers import ExceptionCommand
from utils import s3helpers, email_helper

logger = logging.getLogger(__name__)

S3_BUCKET_B1_ML = 'b1-ml'
EXPECTED_COLS = ['adgroup', 'action', 'source', 'publisher', 'factor']
OEN_ACCOUNT = 305


class Command(ExceptionCommand):

    help = "Sends Post-click KPI Optimization CPA factors in email to OEN"

    @influx.timer('dash.commands.send_oen_postclickkpi_cpa_email_job.running_time')
    def handle(self, *args, **options):
        logger.info('Sending OEN post click kpi optimization CPA factors email')

        oen_ad_groups = [adg.id for adg in models.AdGroup.objects.filter(campaign__account=OEN_ACCOUNT)]

        output = cStringIO.StringIO()
        writer = unicodecsv.writer(output, encoding='utf-8', delimiter=';')
        writer.writerow(EXPECTED_COLS)

        s3_helper = s3helpers.S3Helper(S3_BUCKET_B1_ML)
        f = s3_helper.get('postclick_kpi/siciliana/actionspercost/trim_ratios/agsrcpub/latest/trimratios.tsv')

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

            if int(out['adgroup']) not in oen_ad_groups:
                continue

            out['factor'] = row[2]

            for col in EXPECTED_COLS:
                if col not in out:
                    raise Exception('Unexpected factor key in factor row: %s' % factor_row)

            writer.writerow([out[c] for c in EXPECTED_COLS])

        factors = output.getvalue()

        email_helper.send_oen_postclickkpi_cpa_factors_email(factors)
        influx.gauge('dash.commands.send_oen_postclickkpi_cpa_email_job.num_factors', len(factors.splitlines()))
