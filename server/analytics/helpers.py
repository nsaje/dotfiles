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
    for key, obj in lookup.items():
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


def get_stats_multiple(date, **lookup):
    """
    Get RS stats for a certan date.
    Usage: get_spend(date, **lookup)
    Examples:
     - get_stats_multiple(date, ad_group=ad_group_list)
     - get_stats_multiple(date, campaign=campaign_list)
     - get_stats_multiple(date, account=account_list)
     - get_stats_multiple(date, agency=agency_list)

    Only one lookup entry is expected (ad_group, campaign, account or agency).
    """
    if not lookup:
        return None
    context = {
        'date': str(date),
    }
    for key, objects in lookup.items():
        if objects is None:
            continue
        context['key'] = key
        context['value'] = ','.join([str(obj.pk) for obj in objects])
        break
    sql = backtosql.generate_sql('sql/helpers_get_stats_multiple.sql', context)
    with db.get_stats_cursor() as c:
        c.execute(sql)
        return {
            row[key + '_id']: row for row in db.dictfetchall(c)
        }
