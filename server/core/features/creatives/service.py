from django.db import transaction

import core.features.creatives
import core.models
import dash.constants


@transaction.atomic
def migrate_for_account(account_id, *, offset=0, limit=1000):
    """
    Function is used only for product testing.
    TODO (msuber): implement proper migration.
    """
    account = core.models.Account.objects.get(id=account_id)
    if account.archived:
        return

    queryset = (
        core.models.ContentAd.objects.filter(ad_group__campaign__account_id=account_id)
        .filter(type=dash.constants.AdType.CONTENT)
        .order_by("-created_dt")
        .exclude_archived()
    )
    ads = list(queryset[offset : offset + limit])
    if len(ads) == 0:
        return

    [core.features.creatives.Creative.objects.create_from_ad(None, ad) for ad in ads]
