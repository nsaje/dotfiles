import time

from django.db import transaction
from django.db.models import Q

import core.models
import dash.constants
import utils.exc
from utils import zlogging

from . import exceptions

logger = zlogging.getLogger(__name__)
LOGGER_UPDATE_BATCH_SIZE = 512
PAUSE_INTERVAL = 30
NAS_TAG = "biz/NES"


def deprecate_shell(source_ids):
    sources_deprecated = []
    ad_group_sources_paused = set()

    for source_id in source_ids:
        source = core.models.Source.objects.get(id=int(source_id))
        if source.deprecated:
            continue

        ad_group_sources = (
            core.models.AdGroupSource.objects.exclude(ad_group__campaign__account__id=305)
            .filter(source=source, settings__state=dash.constants.AdGroupSourceSettingsState.ACTIVE)
            .select_related("settings")
        )
        total_ags_count = ad_group_sources.count()
        total_ags_paused = 0

        with transaction.atomic():
            source.deprecated = True
            source.save()
            sources_deprecated.append(source.pk)

            for ags in ad_group_sources:
                ags.settings.update(state=dash.constants.AdGroupSourceSettingsState.INACTIVE, skip_notification=True)
                ad_group_sources_paused.add(ags.id)
                total_ags_paused += 1

                if total_ags_paused % LOGGER_UPDATE_BATCH_SIZE == 0:
                    logger.info(
                        "Ad group source pausing of source done.",
                        source=source.name,
                        source_id=source.id,
                        total=(total_ags_paused / total_ags_count) * 100,
                    )

                if total_ags_paused % PAUSE_INTERVAL == 0:
                    time.sleep(1)

        logger.info("Source deprecated successfully", source=source.name)

    logger.info(
        "Sources deprecated", num_sources_deprecated=len(sources_deprecated), sources_deprecated=sources_deprecated
    )
    logger.info("Ad group sources paused", num_ad_group_sources_paused=len(ad_group_sources_paused))

    return ad_group_sources_paused


def complete_release_shell(source_ids):
    sources = []
    for source_id in source_ids:
        try:
            source = core.models.Source.objects.get(id=int(source_id))
            sources.add(source)

        except core.models.Source.DoesNotExist:
            raise utils.exc.MissingDataError("Source does not exist")

    complete_release(sources)


def complete_release(sources):
    accounts = core.models.Account.objects.filter(settings__auto_add_new_sources=True).select_related("agency")

    for source in sources:
        release_source(None, source, account_list=accounts, skip_validation=True)
        auto_add_new_ad_group_sources(source)


def auto_add_new_ad_group_sources(source):
    ad_groups = core.models.AdGroup.objects.exclude(campaign__account__id=305).filter(
        Q(campaign__account__settings__auto_add_new_sources=True)
        & Q(settings__archived=False)
        & (
            Q(settings__autopilot_state=dash.constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET)
            | Q(settings__b1_sources_group_enabled=True)
        )
    )

    count_available = 0
    count_not_allowed = 0
    count_retargeting_not_supported = 0
    count_video_not_supported = 0
    count_display_not_supported = 0
    total_count = len(ad_groups)

    for ad_group in ad_groups:
        try:
            core.models.AdGroupSource.objects.create(None, ad_group, source, skip_notification=True)

        except core.models.ad_group_source.exceptions.SourceAlreadyExists:
            pass

        except core.models.ad_group_source.exceptions.SourceNotAllowed:
            count_not_allowed += 1
            continue
        except core.models.ad_group_source.exceptions.RetargetingNotSupported:
            count_retargeting_not_supported += 1
            continue
        except core.models.ad_group_source.exceptions.VideoNotSupported:
            count_video_not_supported += 1
            continue
        except core.models.ad_group_source.exceptions.DisplayNotSupported:
            count_display_not_supported += 1
            continue

        count_available += 1
        total_done = (
            count_available
            + count_not_allowed
            + count_retargeting_not_supported
            + count_video_not_supported
            + count_display_not_supported
        )

        if total_done % LOGGER_UPDATE_BATCH_SIZE == 0:
            logger.info(
                "Auto adding of source to ad groups done.",
                source=source.name,
                source_id=source.id,
                total=(total_done / total_count) * 100,
            )

    count_not_available = (
        count_not_allowed + count_retargeting_not_supported + count_video_not_supported + count_display_not_supported
    )

    logger.info(
        "Source not added to ad groups due to not being allowed "
        "retargeting not supported video not supported  display not supported",
        source=source.name,
        source_id=source.id,
        count_not_allowed=count_not_allowed,
        count_retargeting_not_supported=count_retargeting_not_supported,
        count_video_not_supported=count_video_not_supported,
        count_display_not_supported=count_display_not_supported,
    )
    logger.info(
        "Auto adding of source to ad groups DONE. It is available on ad groups",
        source=source.name,
        source_id=source.id,
        count_available=count_available,
        count_not_available=count_not_available,
    )

    return count_available, count_not_available


@transaction.atomic
def release_source(request, source, account_list=None, skip_validation=False):
    if not skip_validation and source.released:
        raise exceptions.SourceAlreadyReleased("Source already released")

    accounts = account_list or core.models.Account.objects.filter(settings__auto_add_new_sources=True).select_related(
        "agency"
    )
    n_allowed_on = 0

    for account in accounts:
        if (
            not account.agency
            or not account.agency.available_sources.exists()
            and not account.agency.allowed_sources.exists()
            and not account.agency.entity_tags.filter(name__icontains=NAS_TAG)
        ):
            account.allowed_sources.add(source)
            changes_text = "{} added to allowed media sources".format(source.name)
            account.write_history(
                changes_text,
                action_type=dash.constants.HistoryActionType.SETTINGS_CHANGE,
                user=getattr(request, "user", None),
            )
            logger.info(
                "Source allowed on account.",
                source=source.name,
                source_id=source.id,
                account=account.name,
                account_id=account.id,
            )
            n_allowed_on += 1
    logger.info("Source allowed on accounts.", source=source.name, source_id=source.id, n_allowed_on=n_allowed_on)

    agencies = core.models.Agency.objects.filter(available_sources__isnull=False, is_disabled=False).exclude(
        entity_tags__name__icontains=NAS_TAG
    )
    n_available_on = 0
    for agency in agencies:
        agency.available_sources.add(source)
        changes_text = "{} added to available media sources".format(source.name)
        agency.write_history(
            changes_text,
            action_type=dash.constants.HistoryActionType.SETTINGS_CHANGE,
            user=getattr(request, "user", None),
        )
        logger.info(
            "Source available on agency.",
            source=source.name,
            source_id=source.id,
            agency_name=agency.name,
            agency_id=agency.id,
        )
        n_available_on += 1

    logger.info("Source available on agencies.", source=source.name, source_id=source.id, n_allowed_on=n_available_on)

    source.released = True
    source.save()

    return n_allowed_on, n_available_on


def unrelease_source(request, source):
    if not source.released:
        raise exceptions.SourceAlreadyUnreleased("Source already unreleased")

    source.released = False
    source.save()
