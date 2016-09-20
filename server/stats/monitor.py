import logging
import datetime

from django.db.models import F, Sum

import reports.models
import reports.projections

logger = logging.getLogger('stats.monitor')


def audit_spend_integrity(date):
    # TODO
    pass


def audit_spend_patterns(date=None, threshold=0.8, first_in_month_threshold=0.6, day_range=3):
    if date is None:
        date = datetime.datetime.utcnow().date() - datetime.timedelta(1)
    total_spend = Sum(F('media_spend_nano') + F('data_spend_nano') + F('license_fee_nano'))
    result = reports.models.BudgetDailyStatement.objects.filter(
        date__lte=date,
        date__gte=date - datetime.timedelta(day_range),
    ).values('date').annotate(
        total=total_spend
    ).order_by('date')
    totals = [row['total'] for row in result]
    changes = [
        (date + datetime.timedelta(-x), float(totals[-x - 1]) / totals[-x - 2])
        for x in xrange(0, day_range - 1)
    ]
    alarming_dates = [
        (d, change) for d, change in changes
        if d.day == 1 and change < first_in_month_threshold or d.day != 1 and change < threshold
    ]
    return not any(alarming_dates), alarming_dates


def audit_pacing(date):
    # TODO
    pass
