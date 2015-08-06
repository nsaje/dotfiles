"""
This script checks(for now) whether for an adgroup
all content ads have corresponding content ad sources for non deprecated adgroup sources.
"""


import sys
import logging
import dash


from optparse import make_option
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--adgroup', help='Adgroup id.'),
    )

    def handle(self, *args, **options):
        try:
            adgroup_id = int(options['adgroup'])
        except:
            logging.exception("Failed parsing command line arguments")
            sys.exit(1)

        adgroup_sources = dash.models.AdGroupSource.objects.filter(ad_group__id=adgroup_id, source__deprecated=False)
        content_ad_ids = dash.models.ContentAd.objects.filter(ad_group__id=adgroup_id).values_list('id', flat=True)
        count_content_ad_ids = len(content_ad_ids)

        integrity_check = True
        errors = []
        for adgroup_source in adgroup_sources:
            count_content_ad_sources = len(dash.models.ContentAdSource.objects.filter(
                content_ad__id__in=content_ad_ids, source__id = adgroup_source.source.id))
            if count_content_ad_sources != count_content_ad_ids:
                integrity_check = False
                errors.append("integrity error - missing content ad sources({c1}/{c2}) for source {name}".format(
                    c1=count_content_ad_sources,
                    c2=count_content_ad_ids,
                    name=adgroup_source.source.name))

        if integrity_check:
            print("AdGroup {adgid} OK".format(adgid=adgroup_id))
        else:
            print("AdGroup {adgid} NOK".format(adgid=adgroup_id))
            for err in errors:
                print(err)
