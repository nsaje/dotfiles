import logging
import cStringIO
import textwrap

import influx
import unicodecsv
from django.core.mail import EmailMessage
from django.conf import settings

from dash import models
from utils.command_helpers import ExceptionCommand
from utils import s3helpers

logger = logging.getLogger(__name__)

S3_BUCKET_B1_ML = 'b1-ml'
EXPECTED_COLS = ['adgroup', 'action', 'source', 'publisher', 'factor']
OEN_ACCOUNT = 305
OEN_CPA_EMAIL = 'davorin.kopic@zemanta.com' #'abc@outbrain.com' # TODO


class Command(ExceptionCommand):
    @influx.timer('dash.scheduled_reports.send_scheduled_reports_job') # TODO fix
    def handle(self, *args, **options):
        logger.info('Sending OEN post click kpi optimization CPA factors email')

        # oen_ad_groups = [adg.id for adg in models.AdGroup.objects.filter(campaign__account=OEN_ACCOUNT)]
        oen_ad_groups = [2312]
        print oen_ad_groups

        output = cStringIO.StringIO()
        writer = unicodecsv.writer(output, encoding='utf-8', delimiter=';')
        writer.writerow(EXPECTED_COLS)

        # read from s3
        s3_helper = s3helpers.S3Helper(S3_BUCKET_B1_ML)
        f = s3_helper.get('postclick_kpi/siciliana/actionspercost/trim_ratios/agsrcpub/latest/trimratios.tsv')

        for factor_row in f.splitlines():
            row = factor_row.split('\t')
            out = {}

            for part in row[1].split(';'):
                s = part.split('=')
                if len(s) != 2:
                    print 'aaaaa' # todo
                out[s[0]] = s[1]

            if int(out['adgroup']) not in oen_ad_groups:
                continue

            out['factor'] = row[2]

            for col in EXPECTED_COLS:
                if col not in out:
                    print 'errorrrrr' # todo
                    continue

            writer.writerow([out[c] for c in EXPECTED_COLS])

        print output.getvalue() # TODO

        email = EmailMessage(
            'Zemanta CPA Optimization Factors',
            textwrap.dedent(u"""\
                Hi OEN,

                Please find current CPA optimization factors attached.

                Best wishes,
                Zemanta
                """),
            'Zemanta <{}>'.format(settings.FROM_EMAIL),
            [OEN_CPA_EMAIL],
        )
        email.attach('cpa_factors.csv', output.getvalue(), 'text/csv')
        email.send()
