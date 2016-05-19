import datetime
import os
import django
from dateutil.parser import parse
from optparse import OptionParser
from dash import constants

os.environ['DJANGO_SETTINGS_MODULE'] = 'server.settings'
django.setup()

# django has to be started before the models are imported
from django.db.models import Sum  # noqa
from dash.models import AdGroup, AdGroupSource  # noqa
from reports.models import ContentAdStats  # noqa
from automation import campaign_stop  # noqa


def create_overspend_report(date, ad_group_id, debug_print):
    if ad_group_id:
        ad_groups = AdGroup.objects.filter(id=ad_group_id).prefetch_related('sources', 'contentad_set')
    else:
        ad_groups = AdGroup.objects.all().prefetch_related('sources', 'contentad_set')
    ad_groups = ad_groups.exclude_archived()
    ad_group_settings = campaign_stop._get_ag_settings_dict(date, ad_groups)
    next_day = date + datetime.timedelta(days=1)

    # all ad groups
    for ad_group in ad_groups:
        ad_group_name = ad_group.name.encode(errors='replace')
        media_sources = ad_group.sources.filter(source_type__type=constants.SourceType.B1)
        content_ads = ad_group.contentad_set.all()

        # all source for this ad group
        ad_group_sources = AdGroupSource.objects.filter(ad_group=ad_group, source__in=media_sources).select_related(
            'source')
        ad_group_sources_settings = campaign_stop._get_sources_settings_dict(next_day, ad_group_sources)
        for ad_group_source in ad_group_sources:
            media_source = ad_group_source.source
            media_source_name = media_source.name.encode(errors='replace')

            #  daily budget
            daily_budget = campaign_stop._get_source_max_daily_budget(date, ad_group_source,
                                                                      ad_group_settings[ad_group.id],
                                                                      ad_group_sources_settings[ad_group_source.id])
            if daily_budget == 0:
                continue

            # daily spent
            daily_spent = ContentAdStats.objects.filter(source=media_source,
                                                        date=date,
                                                        content_ad__in=content_ads).aggregate(Sum('cost_cc'))
            daily_spent = (daily_spent['cost_cc__sum'] or 0) / float(10000)

            # diff
            diff = daily_spent - float(daily_budget)
            print_result(ad_group, ad_group_name, media_source, media_source_name, daily_budget, daily_spent, diff,
                         debug_print)


def print_result(ad_group, ad_group_name, media_source, media_source_name, daily_budget, daily_spent, diff,
                 debug_print):
    if diff > 0:
        result_string = 'OVERSPENT: AdGroup {} [id={}], MediaSource: {} [id={}], Daily budget: {}, ' \
                        'Daily spent: {}, DIFF: {}'.format(
                            ad_group_name, ad_group.id, media_source_name, media_source.id, daily_budget,
                            daily_spent, diff)

        # if overspend exceeds 1$ then mark it
        if diff > 1:
            result_string += ' *****************'
        print(result_string)
    elif debug_print:
        result_string = 'OK: AdGroup {} [id={}], MediaSource: {} [id={}], Daily budget: {}, ' \
                        'Daily spent: {}'.format(
                            ad_group_name, ad_group.id, media_source_name, media_source.id, daily_budget,
                            daily_spent)
        print(result_string)


parser = OptionParser()
parser.add_option('-d', '--debug', dest='debug', action="store_true", default=False)
(options, args) = parser.parse_args()

date = None
if len(args) >= 1:
    date = parse(args[0])
    print('Checking overspending only for day ' + str(date))

ad_group_id = None
if len(args) >= 2:
    ad_group_id = int(args[1])
    print('Checking overspending only for AdGroup with id ' + str(ad_group_id))

if date:
    create_overspend_report(date.date(), ad_group_id, options.debug)
else:
    date = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)

    # print last 7 days
    for i in range(7):
        print('Checking overspending for day ' + str(date))
        create_overspend_report(date, ad_group_id, options.debug)
        date -= datetime.timedelta(days=1)
