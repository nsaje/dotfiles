import logging

from django.http import HttpRequest
from django.conf import settings
from utils.command_helpers import ExceptionCommand

from dash import models
from dash import publisher_group_helpers
from zemauth.models import User as ZemUser

logger = logging.getLogger(__name__)


# FIXME: obsolete after 2017-03-01
class Command(ExceptionCommand):

    help = "Migrate old blacklists to the new blacklists with publisher groups"

    def add_arguments(self, parser):
        parser.add_argument('--ad_group_id', type=int)

    def handle(self, *args, **options):
        ad_groups = models.AdGroup.objects.all().exclude_archived()\
                                                .select_related('campaign', 'campaign__account')\
                                                .order_by('-pk')

        if options.get('ad_group_id'):
            ad_groups = ad_groups.filter(pk=options['ad_group_id'])

        campaigns = models.Campaign.objects.filter(pk__in=ad_groups.values_list('campaign_id', flat=True).distinct())
        accounts = models.Account.objects.filter(
            pk__in=ad_groups.values_list('campaign__account_id', flat=True).distinct())

        request = HttpRequest()
        request.user = ZemUser.objects.get(pk=293)

        for ad_group in ad_groups:
            print "Migrating ad group {}:".format(ad_group.id),
            old_blacklist = models.PublisherBlacklist.objects.filter(ad_group=ad_group)
            if not old_blacklist.exists():
                print "SKIP (no blacklist)"
                continue
            publisher_group_helpers.blacklist_publishers(request, convert_to_dicts(old_blacklist), ad_group)
            print "SUCCESS ({} blacklisted, {} entries in publisher group)".format(
                old_blacklist.count(), ad_group.default_blacklist.entries.all().count())

        for campaign in campaigns:
            print "Migrating campaign {}:".format(campaign.id),
            old_blacklist = models.PublisherBlacklist.objects.filter(campaign=campaign)
            if not old_blacklist.exists():
                print "SKIP (no blacklist)"
                continue
            publisher_group_helpers.blacklist_publishers(request, convert_to_dicts(old_blacklist), campaign)
            print "SUCCESS ({} blacklisted, {} entries in publisher group)".format(
                old_blacklist.count(), campaign.default_blacklist.entries.all().count())

        for account in accounts:
            print "Migrating account {}:".format(campaign.id),
            old_blacklist = models.PublisherBlacklist.objects.filter(account=account)
            if not old_blacklist.exists():
                print "SKIP (no blacklist)"
                continue
            publisher_group_helpers.blacklist_publishers(request, convert_to_dicts(old_blacklist), account)
            print "SUCCESS ({} blacklisted, {} entries in publisher group)".format(
                old_blacklist.count(), account.default_blacklist.entries.all().count())

        if not options.get('ad_group_id'):
            print "Migrating global blacklist {}:".format(settings.GLOBAL_BLACKLIST_ID),
            old_blacklist = models.PublisherBlacklist.objects.filter(everywhere=True)
            publisher_group_helpers.blacklist_publishers(request, convert_to_dicts(old_blacklist), None)
            print "SUCCESS ({} blacklisted, {} entries in publisher group)".format(
                old_blacklist.count(), publisher_group_helpers.get_global_blacklist().entries.all().count())


def convert_to_dicts(old_blacklist):
    entry_dicts = []
    for entry in old_blacklist:
        entry_dicts.append({
            'publisher': entry.name,
            'source': entry.source,
            'include_subdomains': True,
        })
    return entry_dicts
