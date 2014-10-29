import datetime
import dateutil.parser

import dash.models


def last_n_days(n):
    '''
    Returns last n days including today.
    '''
    today = datetime.datetime.utcnow().date()
    return [today - datetime.timedelta(days=x) for x in xrange(n)]


def get_ad_group_sources(ad_group_ids=None, source_ids=None):
    ad_group_sources = dash.models.AdGroupSource.objects.all()

    if ad_group_ids is not None:
        ad_group_sources = ad_group_sources.filter(ad_group__in=ad_group_ids)

    if source_ids is not None:
        ad_group_sources = ad_group_sources.filter(source__in=source_ids)

    return ad_group_sources


def parse_id_list(options, field_name):
    if not options[field_name]:
        return

    return [int(aid) for aid in options[field_name].split(',')]


def parse_date(options, field_name='date'):
    if not options[field_name]:
        return

    return dateutil.parser.parse(options[field_name]).date()
