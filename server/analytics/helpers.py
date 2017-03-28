import backtosql
from redshiftapi import db


def get_spend(date, **lookup):
    """
    Get spend after a certan date.
    Usage: get_spend(date, **lookup)
    Examples:
     - get_spend(date, ad_group=ad_group)
     - get_spend(date, campaign=campaign)
     - get_spend(date, account=account)
     - get_spend(date, agency=agency)

    Only one lookup entry is expected (ad group, campaign, account or agency).
    """
    if not lookup:
        return None
    context = {
        'date': str(date),
        'operator': '=',
    }
    for key, obj in lookup.iteritems():
        if obj is None:
            continue
        context['key'] = key
        context['value'] = obj.pk
        if key == 'agency':
            accounts = obj.account_set.all()
            if not accounts:
                return None
            context['key'] = 'account'
            context['operator'] = 'IN'
            context['value'] = '(' + ','.join(str(acc.pk) for acc in accounts) + ')'
        break
    sql = backtosql.generate_sql('sql/helpers_get_spend.sql', context)
    with db.get_stats_cursor() as c:
        c.execute(sql)
        return db.dictfetchall(c)
