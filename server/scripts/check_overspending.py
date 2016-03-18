import datetime
import os
import django

os.environ['DJANGO_SETTINGS_MODULE'] = 'server.settings'
django.setup()

from optparse import OptionParser
from dateutil.parser import parse
from django.db.models import Sum
from dash import constants
from dash.models import AdGroup, AdGroupSourceSettings, AdGroupSource
from reports.models import ContentAdStats
from automation import campaign_stop


def create_overspend_report(date, ad_group_id, debug_print):
    if ad_group_id:
        ad_groups = AdGroup.objects.filter(id=ad_group_id).prefetch_related('sources')
    else:
        ad_groups = AdGroup.objects.all().prefetch_related('sources')

    # all ad groups
    for ad_group in ad_groups.iterator():
        if ad_group.is_archived():
            continue

        ad_group_name = unicode(ad_group.name)
        media_sources = ad_group.sources.filter(source_type__type=constants.SourceType.B1)
        content_ads = ad_group.contentad_set.all()

        ad_group_sources = AdGroupSource.objects.filter(ad_group=ad_group, source__in=media_sources)
        ad_group_sources_map = {ags.source: ags for ags in ad_group_sources}

        # all media source for this ad group
        for media_source in media_sources:
            media_source_name = unicode(media_source.name)

            #  daily budget
            ad_group_source = ad_group_sources_map[media_source]
            next_day = date + datetime.timedelta(days=1)
            ad_group_settings = AdGroupSourceSettings.objects.filter(ad_group_source=ad_group_source,
                                                                     created_dt__lt=next_day)
            daily_budget = campaign_stop._get_source_max_daily_budget(date, ad_group_source, ad_group_settings)
            if daily_budget == 0:
                continue

            # daily spent
            daily_spent = ContentAdStats.objects.filter(source=media_source,
                                                        date=date,
                                                        content_ad__in=content_ads).aggregate(Sum('cost_cc'))
            daily_spent = (daily_spent['cost_cc__sum'] or 0) / float(10000)

            # diff
            diff = daily_spent - float(daily_budget)
            if diff > 0:
                try:
                    result_string = 'OVERSPENT: AdGroup {} [id={}], MediaSource: {} [id={}], Daily budget: {}, ' \
                                    'Daily spent: {}, DIFF: {}'.format(
                                        ad_group_name, ad_group.id, media_source_name, media_source.id, daily_budget,
                                        daily_spent, diff)
                    print(result_string)
                except UnicodeEncodeError:
                    print('Error printing AdGroup.id=' + ad_group.id)
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

ad_group_id = None
if len(args) >= 2:
    ad_group_id = int(args[1])
    print('Checking overspending only for AdGroup with id ' + str(ad_group_id))

if date:
    create_overspend_report(date.date(), ad_group_id, options.debug)
else:
    date = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)

    while True:
        print('Checking overspending for day ' + str(date))
        create_overspend_report(date, ad_group_id, options.debug)
        date -= datetime.timedelta(days=1)
