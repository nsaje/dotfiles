import os
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "server.settings"
django.setup()

# django has to be started before the models are imported
from dash.models import Campaign, AdGroup, ContentAdSource, Account  # noqa

"""
This script check how many ContentAds doesn't have a tracker_urls set. ContentAds are filtered by specified exchange.
It goes through all accounts, campaign, adgroups and contentads and filters all archived out. Then it prints the results
per account per campaign per adgroup.
"""


def check_tracker_urls(exchange):
    content_ad_sources = ContentAdSource.objects.filter(
        source__tracking_slug=exchange, content_ad__archived=False
    ).select_related(
        "content_ad",
        "content_ad__ad_group",
        "content_ad__ad_group__campaign",
        "content_ad__ad_group__campaign__account",
    )

    nonarchived_ad_groups = AdGroup.objects.all().exclude_archived().values_list("id", flat=True)
    nonarchived_campaigns = Campaign.objects.all().exclude_archived().values_list("id", flat=True)
    nonarchived_accounts = Account.objects.all().exclude_archived().values_list("id", flat=True)

    result_dict = {}
    for content_ad_source in content_ad_sources:
        content_ad = content_ad_source.content_ad

        ad_group = content_ad.ad_group
        if ad_group.id not in nonarchived_ad_groups:
            continue

        campaign = ad_group.campaign
        if campaign.id not in nonarchived_campaigns:
            continue

        account = campaign.account
        if account.id not in nonarchived_accounts:
            continue

        account_dict = result_dict.get(account.name, {})
        campaign_dict = account_dict.get(campaign.name, {})
        count_list = campaign_dict.get(ad_group.name, [0, 0])
        if content_ad.tracker_urls:
            count_list[0] += 1
        else:
            count_list[1] += 1

        campaign_dict[ad_group.name] = count_list
        account_dict[campaign.name] = campaign_dict
        result_dict[account.name] = account_dict

    for acc, acc_dict in result_dict.items():
        print(("\nAccount: " + acc + "\t\t[TRACKED: %s FREE: %s]" % count_for_account(acc_dict)))
        for campaign, campaign_dict in acc_dict.items():
            print(("Campaign: " + campaign + "\t\t[TRACKED: %s FREE: %s]" % count_for_campaign(campaign_dict)))
            for ag, values in campaign_dict.items():
                print(("AdGroup: " + ag + "\t\t[TRACKED: %s FREE: %s]" % (values[0], values[1])))


def count_for_account(acc_dict):
    tracked, free = 0, 0
    for camp, camp_dict in acc_dict.items():
        for ag, values in camp_dict.items():
            tracked += values[0]
            free += values[1]
    return tracked, free


def count_for_campaign(camp_dict):
    tracked, free = 0, 0
    for ag, values in camp_dict.items():
        tracked += values[0]
        free += values[1]
    return tracked, free


check_tracker_urls("yahoo")
