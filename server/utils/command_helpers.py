import datetime
import dateutil.parser

from dash.models import AdGroup


def yesterday():
    return datetime.date.today() - datetime.timedelta(days=1)


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


def parse_date(options):
    if not options['date']:
        return

    return dateutil.parser.parse(options['date']).date()
