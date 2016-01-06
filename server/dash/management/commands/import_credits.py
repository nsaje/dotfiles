import math
import datetime

import unicodecsv as csv
from django.core.management.base import BaseCommand

import dash.models
import reports.models
import dash.bcm_helpers
from django.db.models import Sum

LINE_CORRECTIONS, LINE_IN_Z1, LINE_CREDIT_ID, LINE_ACCOUNT_ID, LINE_VALID_FROM, LINE_VALID_TO, LINE_DATE_SIGNED, LINE_TOTAL_AMOUNT, LINE_LICENSE_TYPE, LINE_LICENSE_PERCENT, LINE_LICENSE_TOTAL, LINE_MEDIA_AMOUNT, LINE_NOTES, LINE_PDF = range(14)

def are_date_ranges_overlaping(dates):
    if len(dates) <= 1:
        return False
    sorted_dates = dates[:]
    sorted(sorted_dates, key=lambda s, e: s)
    prev_e = sorted_dates[0]
    for s, e in sorted_dates[1:]:
        if prev_e >= s:
            return True
        prev_e = e
    return False

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
                    account=line[LINE_ACCOUNT_ID],
                    valid_from=line[LINE_VALID_FROM],
                    valid_to=line[LINE_VALID_TO],
                    amount=line[LINE_TOTAL_AMOUNT],
                    notes=line[LINE_NOTES] + ' ' + line[LINE_PDF],
                )
                credit_license_type = line[LINE_LICENSE_TYPE]

                if 'Flat' in credit_license_type:
                    credit['license_fee'] = 0
                    credit['amount'] = line[LINE_MEDIA_AMOUNT]
                elif '%' in credit_license_type:
                    credit['license_fee'] = line[LINE_LICENSE_PERCENT]
                else:
                    skipped += 1
                    continue
                
                all_credits.append(dash.bcm_helpers.clean_credit_input(**credit))
        ok, duplicates, with_errors, budgets = 0, 0, 0, 0
        finished_accounts = set()
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
                imported_credit = dash.bcm_helpers.import_credit(*credit)
                ok += 1
            except:
                print 'Error with:', credit
                with_errors += 1
                continue

            ### Automatic budget creation
            raw_campaigns = dash.models.Campaign.objects.filter(account=imported_credit.account)
            campaigns = []
            for c in raw_campaigns:
                stats = reports.models.ContentAdStats.objects\
                                                         .filter(content_ad__ad_group__campaign_id=c.id)\
                                                         .aggregate(cost_cc_sum=Sum('cost_cc'),
                                                                    data_cost_cc_sum=Sum('data_cost_cc'))
                cost = (stats['cost_cc_sum'] or 0) + (stats['data_cost_cc_sum'] or 0)
                if cost > 0:
                    campaigns.append(c)

            if imported_credit.is_active():
                continue
                    
            if len(campaigns) == 1:
                dash.models.BudgetLineItem.objects.create(
                    credit=imported_credit,
                    campaign=campaigns[0],
                    start_date=imported_credit.start_date,
                    end_date=imported_credit.end_date,
                    comment='Generated automatically with credit import',
                    amount=imported_credit.amount,
                )
                budgets += 1
                print 'Generated budget for campaign {} with rule: only 1 campaign'.format(
                    campaigns[0].pk
                )
                finished_accounts.add(imported_credit.account.pk)
                continue
            
        accounts_without_credits = set()
        for account in dash.models.Account.objects.all():
            account_credits = account.credits.all()
            campaigns = dash.models.Campaign.objects.filter(account=account)
            if account.pk in finished_accounts:
                continue
            if 'New account' in account.name:
                continue            
            if not account_credits:
                accounts_without_credits.add(account.pk)
                continue
            if len(account_credits) == 1 and len(campaigns) > 1:
                credit = account_credits[0]
                if credit.budgets.all().count() > 0:
                    continue
                if credit.is_active():
                    continue
                totals = {}
                for campaign in campaigns:
                    stats = reports.models.ContentAdStats.objects\
                                                         .filter(content_ad__ad_group__campaign_id=campaign.id)\
                                                         .aggregate(cost_cc_sum=Sum('cost_cc'),
                                                                    data_cost_cc_sum=Sum('data_cost_cc'))
                    
                    if stats['cost_cc_sum'] is None:
                        continue
                    cost = (stats['cost_cc_sum'] or 0) + (stats['data_cost_cc_sum'] or 0)
                    total = int(math.ceil(cost * (1 + credit.license_fee) / 10000))
                    totals[campaign.pk] = total
                if sum(totals.values()) > credit.amount:
                    print 'For credit {}, spend is higher than the budget'.format(credit.pk)
                    continue
                for campaign_id, total in totals.items():
                    dash.models.BudgetLineItem.objects.create(
                        campaign_id=campaign_id,
                        credit=credit,
                        amount=total,
                        start_date=credit.start_date,
                        end_date=credit.end_date,
                        comment='Generated automatically with credit import'
                    )
                    print 'Generated budget for campaign {} with rule: only 1 credit for many campaigns'.format(
                        campaign_id
                    )
                    budgets += 1
                    finished_accounts.add(credit.account.pk)
            
        all_accounts = set([acc.pk for acc in dash.models.Account.objects.all()])
        accounts_without_budgets = all_accounts - accounts_without_credits - finished_accounts
        print 'Account IDS without credits:', ', '.join(map(str, accounts_without_credits))
        print 'Account IDS without budgets:', ', '.join(map(str, accounts_without_budgets))
        print '============================================='
        print '================== Summary =================='
        print ' Inserted:', ok
        print ' Skipped:', skipped
        print ' With errors:', with_errors
        print ' Duplicates:', duplicates
        print ' Automatically created budgets:', budgets
        print ' Accounts without credits:', len(accounts_without_credits)
        print ' Accounts with credits but no budgets:', len(accounts_without_budgets)
        print '============================================='
        
