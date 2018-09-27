from django.db import transaction

import core.models
import utils.exc

from . import exceptions


LOGGER_UPDATE_BATCH_SIZE = 40


def auto_add_new_ad_group_sources(source_id, logger=None):
    try:
        source = core.models.Source.objects.get(id=int(source_id))

    except core.models.Source.DoesNotExist:
        raise utils.exc.MissingDataError("Source does not exist")

    ad_groups = core.models.AdGroup.objects.filter(
        campaign__account__settings__auto_add_new_sources=True, settings__archived=False
    )
    count_available = 0
    count_not_available = 0
    total_count = len(ad_groups)

    for ad_group in ad_groups:
        try:
            core.models.AdGroupSource.objects.create(None, ad_group, source, skip_notification=True)

        except core.models.ad_group_source.exceptions.SourceAlreadyExists:
            pass

        except (
            core.models.ad_group_source.exceptions.SourceNotAllowed,
            core.models.ad_group_source.exceptions.RetargetingNotSupported,
            core.models.ad_group_source.exceptions.VideoNotSupported,
        ):
            count_not_available += 1
            continue

        count_available += 1

        total_done = count_available + count_not_available
        if logger and total_done % LOGGER_UPDATE_BATCH_SIZE == 0:
            logger.info("Auto adding of sources to ad groups {}%% done.".format((total_done / total_count) * 100))

    return count_available, count_not_available


@transaction.atomic
def release_source(request, source):
    if source.released:
        raise exceptions.SourceAlreadyReleased("Source already released")

    accounts = core.models.Account.objects.filter(settings__auto_add_new_sources=True)
    for account in accounts:
        account.allowed_sources.add(source)

    source.released = True
    source.save()

    return len(accounts)


def unrelease_source(request, source):
    if not source.released:
        raise exceptions.SourceAlreadyUnreleased("Source already unreleased")

    source.released = False
    source.save()
