import os
import django

import datetime

# start django first
from optparse import OptionParser

from django.db.models import Sum
from dash import constants
from dateutil.parser import parse

os.environ['DJANGO_SETTINGS_MODULE'] = 'server.settings'
django.setup()

from dash.models import AdGroup, ContentAdSource, ContentAd, AdGroupSourceSettings, AdGroupSource
from reports.models import ContentAdStats


def create_overspend_report(date, ad_group_id, debug_print):
    if ad_group_id:
        ad_groups = AdGroup.objects.filter(id=ad_group_id)
    else:
        ad_groups = AdGroup.objects.all()

    # all ad groups
    for ad_group in ad_groups:
        ad_group_name = unicode(ad_group.name)
        content_ads = ContentAd.objects.filter(ad_group=ad_group)

        # ad content_ad => media sources for this ad group
        content_ad_sources = ContentAdSource.objects.filter(
            content_ad__in=content_ads,
            state=constants.ContentAdSourceState.ACTIVE).distinct('source')
        media_sources = set([c.source for c in content_ad_sources if c.source.name not in ('Yahoo', 'Outbrain')])

        # all media source for this ad group
        for media_source in media_sources:
            media_source_name = unicode(media_source.name)

            #  daily budget
            ad_group_sources = AdGroupSource.objects.filter(ad_group=ad_group, source=media_source)
            next_day = date + datetime.timedelta(days=1)
            ad_group_settings = AdGroupSourceSettings.objects.filter(ad_group_source__in=ad_group_sources,
                                                                     created_dt__lt=next_day,
                                                                     state=constants.AdGroupSourceSettingsState.ACTIVE)
            if ad_group_settings.exists():
                ad_group_settings = ad_group_settings.latest('created_dt')
            else:
                continue

            daily_budget = ad_group_settings.daily_budget_cc
            if daily_budget is None:
                continue

            # yesterday spent
            yesterday_spent = ContentAdStats.objects.filter(source=media_source,
                                                            date=date,
                                                            content_ad__in=content_ads).aggregate(Sum('cost_cc'))
            yesterday_spent = float((yesterday_spent['cost_cc__sum'] or 0) / 10000)

            if yesterday_spent > daily_budget:
                try:
                    result_string = 'OVERSPENT: AdGroup %s [id=%d], MediaSource: %s [id=%d], Daily budget: %d, ' \
                                    'Yesterday spent: %f, DIFF: %f' % (
                                        ad_group_name, ad_group.id, media_source_name, media_source.id, daily_budget,
                                        yesterday_spent, yesterday_spent - float(daily_budget))
                    print(result_string)
                except:
                    print('Exception while printing result for adgroup.id = %d and media_source.id = %d' % (
                        ad_group.id, media_source.id))
            elif debug_print:
                result_string = 'OK: AdGroup %s [id=%d], MediaSource: %s [id=%d], Daily budget: %d, ' \
                                'Yesterday spent: %f' % (
                                    ad_group_name, ad_group.id, media_source_name, media_source.id, daily_budget,
                                    yesterday_spent)
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
    print 'Checking overspending only for AdGroup with id ' + str(ad_group_id)

if date:
    create_overspend_report(date, ad_group_id, options.debug)
else:
    date = datetime.datetime.now()
    date = datetime.date(date.year, date.month, date.day) - datetime.timedelta(days=1)

    while True:
        print 'Checking overspending for day ' + str(date)
        create_overspend_report(date, ad_group_id, options.debug)
        date -= datetime.timedelta(days=1)
