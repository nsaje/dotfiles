import datetime
import dateutil.parser

from dash.models import AdGroup


def last_n_days(n):
    '''
    Returns last n days including today.
    '''
    today = datetime.datetime.utcnow().date()
    return [today - datetime.timedelta(days=x) for x in xrange(n)]


def get_ad_groups(ad_group_ids=None):
    if ad_group_ids is None:
        return AdGroup.objects.all()

    ad_groups = AdGroup.objects.filter(id__in=ad_group_ids).all()

    selected_ids = [ag.id for ag in ad_groups]
    if set(selected_ids) != set(ad_group_ids):
        raise Exception('Missing ad groups: {}'.format(set(ad_group_ids) - set(selected_ids)))

    return ad_groups


def parse_ad_group_ids(options):
    if not options['ad_group_ids']:
        return

    return [int(aid) for aid in options['ad_group_ids'].split(',')]


def parse_date(options, field_name='date'):
    if not options[field_name]:
        return

    return dateutil.parser.parse(options[field_name]).date()
