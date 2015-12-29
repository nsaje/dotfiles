import unicodecsv as csv
from django.core.management.base import BaseCommand

import dash.models
import dash.bcm_helpers

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('csv_file', nargs=1, type=str)
        
    def handle(self, *args, **options):
        all_credits = []
        skipped = 0
        with open(options['csv_file'][0]) as fd:
            for num, line in enumerate(csv.reader(fd, encoding='utf-8')):
                if not num:
                    continue
                credit = dict(
                    account=line[0],
                    valid_from=line[1],
                    valid_to=line[2],
                    amount=line[4],
                    notes=line[8] + ' ' + line[9],
                )
                credit_license_type = line[5]
                if credit_license_type == u'%':
                    credit['total_license_fee'] = line[6]
                elif credit_license_type == u'Flat':
                    credit['license_fee'] = '0%'
                else:
                    skipped += 1
                    continue
                all_credits.append(dash.bcm_helpers.clean_credit_input(**credit))
        ok, duplicates, with_errors = 0, 0, 0
        for credit in all_credits:
            duplicate_credits = dash.models.CreditLineItem.objects.filter(
                    account_id=credit[0],
                    start_date=credit[1],
                    end_date=credit[2],
                    license_fee=credit[4],
                    amount=credit[3]
            )
            if duplicate_credits.count():
                duplicates += 1
                continue
            try:
                dash.bcm_helpers.import_credit(*credit)
                ok += 1
            except:
                print 'Error with:', credit
                with_errors += 1

        print 'Inserted:', ok
        print 'Skipped:', skipped
        print 'With errors:', with_errors
        print 'Duplicates:', duplicates
