import datetime
import influx
import logging
import termcolor

from django.db.models import Q
from utils.command_helpers import ExceptionCommand

from dash import models
from dash import publisher_group_helpers

logger = logging.getLogger(__name__)


class Command(ExceptionCommand):

    help = "Compare the old and the new blacklists"

    def add_arguments(self, parser):
        parser.add_argument('--ad_group_id', type=int)
        parser.add_argument('--show_publishers', action='store_true')
        parser.add_argument('--hide_matching', action='store_true')

    def handle(self, *args, **options):
        ad_groups = models.AdGroup.objects.all().exclude_archived()\
                                                .select_related('campaign', 'campaign__account')\
                                                .order_by('-pk')

        filtered_by_adgroup = False
        if options.get('ad_group_id'):
            ad_groups = ad_groups.filter(pk=options['ad_group_id'])
            filtered_by_adgroup = True

        ad_groups_settings = {x.ad_group_id: x for x
                              in models.AdGroupSettings.objects.filter(ad_group__in=ad_groups).group_current_settings()}
        campaigns_settings = {x.campaign_id: x for x
                              in models.CampaignSettings.objects.filter(
                                  campaign_id__in=ad_groups.values_list('campaign_id', flat=True).distinct())\
                              .group_current_settings()}
        accounts_settings = {x.account_id: x for x
                             in models.AccountSettings.objects.filter(
                                 account_id__in=ad_groups.values_list('campaign__account_id', flat=True).distinct())\
                             .group_current_settings()}

        nr_not_matching = 0
        for ad_group in ad_groups:
            ad_group_settings = ad_groups_settings.get(ad_group.id)
            campaign_settings = campaigns_settings.get(ad_group.campaign_id)
            account_settings = accounts_settings.get(ad_group.campaign.account_id)
            if not ad_group_settings or not campaign_settings or not account_settings:
                continue

            blacklist_groups, whitelist_groups = publisher_group_helpers.concat_publisher_group_targeting(
                ad_group, ad_group_settings, ad_group.campaign, campaign_settings,
                ad_group.campaign.account, account_settings)

            blacklisted_entries = models.PublisherGroupEntry.objects.filter(publisher_group_id__in=blacklist_groups)\
                                                                    .order_by('publisher')\
                                                                    .values_list('publisher', 'source_id')

            old_blacklist = models.PublisherBlacklist.objects.filter(Q(ad_group=ad_group) |
                                                                     Q(campaign=ad_group.campaign) |
                                                                     Q(account=ad_group.campaign.account) |
                                                                     Q(everywhere=True))\
                                                             .order_by('name')\
                                                             .values_list('name', 'source_id')

            matching = set(blacklisted_entries) == set(old_blacklist)
            nr_not_matching += 0 if matching else 1

            if not options.get('hide_matching') or not matching:
                print 'Ad Group Id {} matching {}, new count {}, old count {}, blacklisted groups {}'.format(
                    termcolor.colored(ad_group.id, 'blue', 'on_grey'),
                    termcolor.colored(str(matching), 'green' if matching else 'red'),
                    blacklisted_entries.count(), old_blacklist.count(),
                    ",".join(str(x) for x in blacklist_groups)),

                if options.get('show_publishers'):
                    new_extra = set(blacklisted_entries) - set(old_blacklist)
                    old_extra = set(old_blacklist) - set(blacklisted_entries)
                    print u', new extra: {}, old extra: {}'.format(
                        termcolor.colored(u", ".join(u"{}[{}]".format(*x) for x in new_extra), 'blue'),
                        termcolor.colored(u", ".join(u"{}[{}]".format(*x) for x in old_extra), 'cyan'))
                else:
                    print ''

        if not filtered_by_adgroup:
            print "Logged to influx"
            influx.gauge('blacklisting.old_new_ad_groups_not_matching', nr_not_matching)
