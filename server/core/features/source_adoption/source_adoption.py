from django.db import transaction

import core.entity

from . import exceptions


@transaction.atomic
def release_source(request, source):
    if source.released:
        raise exceptions.SourceAlreadyReleased("Source already released")

    accounts = core.entity.Account.objects.filter(settings__auto_add_new_sources=True)
    for account in accounts:
        account.allowed_sources.add(source)

    ad_groups = core.entity.AdGroup.objects.filter(campaign__account__settings__auto_add_new_sources=True)
    count_released = 0
    count_not_released = 0

    for ad_group in ad_groups:
        try:
            core.entity.AdGroupSource.objects.create(request, ad_group, source)

        except core.entity.adgroup.ad_group_source.exceptions.SourceAlreadyExists:
            pass

        except (
            core.entity.adgroup.ad_group_source.exceptions.SourceNotAllowed,
            core.entity.adgroup.ad_group_source.exceptions.RetargetingNotSupported,
            core.entity.adgroup.ad_group_source.exceptions.VideoNotSupported,
        ):
            count_not_released += 1
            continue

        count_released += 1

    source.released = True
    source.save()

    return count_released, count_not_released


def unrelease_source(request, source):
    if not source.released:
        raise exceptions.SourceAlreadyUnreleased("Source already unreleased")

    source.released = False
    source.save()

    return 0, 0
