from django.conf import settings
from django.db import transaction

import core.common
import core.models
import dash.constants
import dash.retargeting_helper
import utils.exc
import utils.k1_helper
from utils import zlogging

from . import exceptions
from . import model

logger = zlogging.getLogger(__name__)


class AdGroupSourceManager(core.common.BaseManager):
    def _create(self, ad_group, source, ad_review_only=False, write_history=True):
        default_settings = source.get_default_settings()
        ad_group_source = model.AdGroupSource(
            source=source,
            ad_group=ad_group,
            source_credentials=default_settings.credentials,
            can_manage_content_ads=source.can_manage_content_ads(),
            ad_review_only=ad_review_only,
        )
        ad_group_source.save(None)
        return ad_group_source

    @transaction.atomic
    def create(
        self,
        request,
        ad_group,
        source,
        write_history=True,
        k1_sync=True,
        skip_validation=False,
        ad_review_only=False,
        skip_notification=False,
        is_adgroup_creation=False,
        **updates,
    ):
        try:
            # TODO: fix the problem of duplicated entries for "source, adgroup" pairs
            ad_group_source = model.AdGroupSource.objects.filter(source=source, ad_group=ad_group).first()
        except model.AdGroupSource.DoesNotExist:
            ad_group_source = None

        if (
            not skip_validation
            and not ad_review_only
            and not ad_group.campaign.account.allowed_sources.filter(pk=source.id).exists()
        ):
            raise exceptions.SourceNotAllowed(
                "{} media source can not be added because it is not allowed on this account. Please go to account settings and allow it first.".format(
                    source.name
                )
            )

        if not skip_validation and ad_group_source and not ad_group_source.ad_review_only:
            raise exceptions.SourceAlreadyExists(
                "{} media source for ad group {} already exists.".format(source.name, ad_group.id)
            )

        if (
            not skip_validation
            and ad_group.campaign.type == dash.constants.CampaignType.VIDEO
            and not source.supports_video
        ):
            raise exceptions.VideoNotSupported(
                "{} media source can not be added because it does not support video.".format(source.name)
            )

        if (
            not skip_validation
            and ad_group.campaign.type == dash.constants.CampaignType.DISPLAY
            and not source.supports_display
        ):
            raise exceptions.DisplayNotSupported(
                "{} media source can not be added because it does not support display ads.".format(source.name)
            )

        if not ad_group_source:
            ad_group_source = self._create(
                ad_group, source, ad_review_only=ad_review_only, write_history=write_history and not ad_review_only
            )
            ad_group_source.set_initial_settings(
                request,
                ad_group,
                skip_notification=skip_notification,
                write_history=write_history and not ad_review_only,
                is_adgroup_creation=is_adgroup_creation,
                **updates,
            )
        elif ad_group_source.ad_review_only and not ad_review_only:
            self._handle_ad_review_only(ad_group_source, skip_notification)
        else:
            raise Exception("Erroneous case - should not be reachable")

        if write_history and not ad_review_only:
            ad_group.write_history_source_added(request, ad_group_source)

        if not is_adgroup_creation:
            # circular dependency
            from dash import api

            api.add_content_ad_sources(ad_group_source)

        if k1_sync:
            utils.k1_helper.update_ad_group(ad_group, msg="AdGroupSources.put")

        return ad_group_source

    def _handle_ad_review_only(self, ad_group_source, skip_notification=False):
        ad_group_source.ad_review_only = False
        ad_group_source.save()

        ad_group_source.settings.update(
            state=dash.constants.AdGroupSourceSettingsState.ACTIVE,
            skip_validation=True,
            skip_notification=skip_notification,
        )

    @transaction.atomic
    def bulk_create_on_allowed_sources(
        self, request, ad_group, sources=None, write_history=True, k1_sync=True, apply_ad_group_bids=False
    ):
        create_on_sources = ad_group.campaign.account.allowed_sources.all().select_related(
            "source_type", "defaultsourcesettings__credentials"
        )
        if sources:
            create_on_sources = create_on_sources.filter(id__in=[source.id for source in sources])
            not_allowed = set(sources) - set(create_on_sources)
            if not_allowed:
                raise exceptions.SourceNotAllowed(
                    "Source(s) %s not allowed on this account." % (", ".join([source.name for source in not_allowed]))
                )
        added_ad_group_sources = []

        updates = {}
        if apply_ad_group_bids:
            if ad_group.bidding_type == dash.constants.BiddingType.CPC:
                updates["cpc_cc"] = ad_group.settings.cpc
            else:
                updates["cpm"] = ad_group.settings.cpm

        for source in create_on_sources:
            if (
                source.deprecated
                or source.maintenance
                or ad_group.campaign.type == dash.constants.CampaignType.VIDEO
                and not source.supports_video
                or ad_group.campaign.type == dash.constants.CampaignType.DISPLAY
                and not source.supports_display
            ):
                continue

            try:
                ad_group_source = self.create(
                    request,
                    ad_group,
                    source,
                    write_history=False,
                    k1_sync=False,
                    skip_validation=True,
                    skip_notification=True,
                    is_adgroup_creation=True,
                    **updates,
                )
                added_ad_group_sources.append(ad_group_source)
            except utils.exc.MissingDataError:
                # skips ad group sources creation without default sources
                logger.exception("Exception occurred on campaign", campaign=ad_group.campaign_id)
                continue

        ad_group.settings.update_daily_budget(request)

        if write_history:
            raise Exception("Can't write history at this stage")

        if k1_sync and added_ad_group_sources:
            utils.k1_helper.update_ad_group(ad_group, msg="AdGroupSources.put")

        return added_ad_group_sources

    @transaction.atomic
    def clone(self, request, ad_group, source_ad_group_source, write_history=True, k1_sync=True):
        ad_group_source = self._create(
            ad_group, source_ad_group_source.source, ad_review_only=source_ad_group_source.ad_review_only
        )
        if write_history and not ad_group_source.ad_review_only:
            ad_group.write_history_source_added(request, ad_group_source)

        ad_group_source.set_cloned_settings(None, source_ad_group_source)

        if settings.K1_CONSISTENCY_SYNC:
            from dash import api  # TODO circular dependency

            api.add_content_ad_sources(ad_group_source)

        if k1_sync:
            utils.k1_helper.update_ad_group(ad_group, msg="AdGroupSources.put")

        return ad_group_source

    @transaction.atomic
    def bulk_clone_on_allowed_sources(self, request, ad_group, source_ad_group, write_history=True, k1_sync=True):
        ad_group_sources = source_ad_group.adgroupsource_set.all().select_related("source")
        map_source_ad_group_sources = {x.source_id: x for x in ad_group_sources}

        added_ad_group_sources = []
        for source in ad_group.campaign.account.allowed_sources.all():
            if source.maintenance:
                continue

            try:
                if source.id in map_source_ad_group_sources:
                    ad_group_source = self.clone(
                        request, ad_group, map_source_ad_group_sources[source.id], write_history=False, k1_sync=False
                    )
                else:
                    continue

                added_ad_group_sources.append(ad_group_source)
            except utils.exc.MissingDataError:
                # skips ad group sources creation without default sources
                logger.exception("Exception occurred on campaign", campaign=ad_group.campaign_id)
                continue

        if write_history:
            raise Exception("Can't write history at this stage")

        if k1_sync and added_ad_group_sources:
            utils.k1_helper.update_ad_group(ad_group, msg="AdGroupSources.put")

        return added_ad_group_sources

    @transaction.atomic
    def pause_sources(self, request, ad_group_sources):
        for ad_group_source in ad_group_sources:
            ad_group_source.settings.update(request, state=dash.constants.AdGroupSourceSettingsState.INACTIVE)
