# -*- coding: utf-8 -*-
import jsonfield
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models, transaction

from dash import constants, retargeting_helper

import core.features.bcm
import core.common
import core.models
import core.features.history

import utils.email_helper
import utils.exc
import utils.k1_helper
import utils.numbers

from . import exceptions

logger = logging.getLogger(__name__)


class AdGroupSourceManager(core.common.QuerySetManager):
    def _create(self, ad_group, source, ad_review_only=False):
        default_settings = source.get_default_settings()
        ad_group_source = AdGroupSource(
            source=source,
            ad_group=ad_group,
            source_credentials=default_settings.credentials,
            can_manage_content_ads=source.can_manage_content_ads(),
            ad_review_only=ad_review_only,
        )
        ad_group_source.save(None)

        ad_group_source.settings = core.models.settings.AdGroupSourceSettings(ad_group_source=ad_group_source)
        ad_group_source.settings.update_unsafe(None)
        ad_group_source.settings_id = ad_group_source.settings.id
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
        **updates
    ):
        try:
            ad_group_source = AdGroupSource.objects.get(source=source, ad_group=ad_group)
        except AdGroupSource.DoesNotExist:
            ad_group_source = None

        if (
            not skip_validation
            and not ad_review_only
            and not ad_group.campaign.account.allowed_sources.filter(pk=source.id).exists()
        ):
            raise exceptions.SourceNotAllowed("{} media source can not be added to this account.".format(source.name))

        if not skip_validation and ad_group_source and not ad_group_source.ad_review_only:
            raise exceptions.SourceAlreadyExists(
                "{} media source for ad group {} already exists.".format(source.name, ad_group.id)
            )

        if not skip_validation and not retargeting_helper.can_add_source_with_retargeting(source, ad_group.settings):
            raise exceptions.RetargetingNotSupported(
                "{} media source can not be added because it does not support retargeting.".format(source.name)
            )

        if not skip_validation and ad_group.campaign.type == constants.CampaignType.VIDEO and not source.supports_video:
            raise exceptions.VideoNotSupported(
                "{} media source can not be added because it does not support video.".format(source.name)
            )

        if not ad_group_source:
            ad_group_source = self._create(ad_group, source, ad_review_only=ad_review_only)
            ad_group_source.set_initial_settings(request, ad_group, skip_notification=skip_notification, **updates)
        elif ad_group_source.ad_review_only and not ad_review_only:
            self._handle_ad_review_only(ad_group_source, skip_notification)
        else:
            raise Exception("Erroneous case - should not be reachable")

        if write_history and not ad_review_only:
            ad_group.write_history_source_added(request, ad_group_source)

        if settings.K1_CONSISTENCY_SYNC:
            # circular dependency
            from dash import api

            api.add_content_ad_sources(ad_group_source)

        if k1_sync:
            utils.k1_helper.update_ad_group(ad_group.id, msg="AdGroupSources.put")

        return ad_group_source

    def _handle_ad_review_only(self, ad_group_source, skip_notification=False):
        ad_group_source.ad_review_only = False
        ad_group_source.save()

        ad_group_source.settings.update(
            state=constants.AdGroupSourceSettingsState.ACTIVE, skip_validation=True, skip_notification=skip_notification
        )

    @transaction.atomic
    def bulk_create_on_allowed_sources(self, request, ad_group, write_history=True, k1_sync=True):
        sources = ad_group.campaign.account.allowed_sources.all().select_related(
            "source_type", "defaultsourcesettings__credentials"
        )
        added_ad_group_sources = []

        if not retargeting_helper.can_add_source_with_retargeting(sources, ad_group.settings):
            raise utils.exc.ValidationError("Media sources can not be added because some do not support retargeting.")

        for source in sources:
            if (
                source.maintenance
                or ad_group.campaign.type == constants.CampaignType.VIDEO
                and not source.supports_video
            ):
                continue

            try:
                ad_group_source = self.create(
                    request, ad_group, source, write_history=False, k1_sync=False, skip_validation=True
                )
                added_ad_group_sources.append(ad_group_source)
            except utils.exc.MissingDataError:
                # skips ad group sources creation without default sources
                logger.exception("Exception occurred on campaign with id %s", ad_group.campaign_id)
                continue

        if write_history:
            raise Exception("Can't write history at this stage")

        if k1_sync and added_ad_group_sources:
            utils.k1_helper.update_ad_group(ad_group.id, msg="AdGroupSources.put")

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
            utils.k1_helper.update_ad_group(ad_group.id, msg="AdGroupSources.put")

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
                logger.exception("Exception occurred on campaign with id %s", ad_group.campaign_id)
                continue

        if write_history:
            raise Exception("Can't write history at this stage")

        if k1_sync and added_ad_group_sources:
            utils.k1_helper.update_ad_group(ad_group.id, msg="AdGroupSources.put")

        return added_ad_group_sources


class AdGroupSource(models.Model):
    class Meta:
        app_label = "dash"

    source = models.ForeignKey("Source", on_delete=models.PROTECT)
    ad_group = models.ForeignKey("AdGroup", on_delete=models.PROTECT)

    source_credentials = models.ForeignKey("SourceCredentials", null=True, on_delete=models.PROTECT)
    source_campaign_key = jsonfield.JSONField(blank=True, default={})

    last_successful_sync_dt = models.DateTimeField(blank=True, null=True)
    last_successful_reports_sync_dt = models.DateTimeField(blank=True, null=True)
    last_successful_status_sync_dt = models.DateTimeField(blank=True, null=True)
    can_manage_content_ads = models.BooleanField(null=False, blank=False, default=False)

    source_content_ad_id = models.CharField(max_length=100, null=True, blank=True)
    blockers = jsonfield.JSONField(blank=True, default={})

    settings = models.OneToOneField(
        "AdGroupSourceSettings", null=True, blank=True, on_delete=models.PROTECT, related_name="latest_for_entity"
    )
    ad_review_only = models.NullBooleanField(default=None)

    objects = AdGroupSourceManager()

    class QuerySet(models.QuerySet):
        def filter_by_sources(self, sources):
            if not core.models.helpers.should_filter_by_sources(sources):
                return self

            return self.filter(source__in=sources)

        def filter_active(self):
            """
            Returns only ad groups sources that have settings set to active.
            """
            return self.filter(settings__state=constants.AdGroupSourceSettingsState.ACTIVE)

        def filter_can_manage_content_ads(self):
            return self.filter(
                can_manage_content_ads=True,
                source_id__in=core.models.Source.objects.all()
                .filter_can_manage_content_ads()
                .values_list("id", flat=True),
            )

    def set_initial_settings(self, request, ad_group, skip_notification=False, **updates):
        from dash.views import helpers

        if "cpc_cc" not in updates:
            updates["cpc_cc"] = self.source.default_cpc_cc
            if ad_group.settings.is_mobile_only():
                updates["cpc_cc"] = self.source.default_mobile_cpc_cc
            if (
                ad_group.settings.b1_sources_group_enabled
                and ad_group.settings.b1_sources_group_cpc_cc > 0.0
                and self.source.source_type.type == constants.SourceType.B1
            ):
                updates["cpc_cc"] = ad_group.settings.b1_sources_group_cpc_cc
            if ad_group.settings.cpc_cc:
                updates["cpc_cc"] = min(ad_group.settings.cpc_cc, updates["cpc_cc"])
        if "cpm" not in updates:
            updates["cpm"] = self.source.default_cpm
            if ad_group.settings.is_mobile_only():
                updates["cpm"] = self.source.default_mobile_cpm
            if (
                ad_group.settings.b1_sources_group_enabled
                and ad_group.settings.b1_sources_group_cpm is not None  # TODO: CPM Buying: remove after migraton
                and ad_group.settings.b1_sources_group_cpm > 0.0
                and self.source.source_type.type == constants.SourceType.B1
            ):
                updates["cpm"] = ad_group.settings.b1_sources_group_cpm
            if ad_group.settings.max_cpm:
                updates["cpm"] = min(ad_group.settings.max_cpm, updates["cpm"])
        if "state" not in updates:
            if helpers.get_source_initial_state(self):
                updates["state"] = constants.AdGroupSourceSettingsState.ACTIVE
            else:
                updates["state"] = constants.AdGroupSourceSettingsState.INACTIVE
        if "daily_budget_cc" not in updates:
            updates["daily_budget_cc"] = self.source.default_daily_budget_cc

        enabling_autopilot_sources_allowed = helpers.enabling_autopilot_sources_allowed(ad_group, [self])
        if not enabling_autopilot_sources_allowed:
            updates["state"] = constants.AdGroupSourceSettingsState.INACTIVE

        self.settings.update(
            request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            skip_notification=skip_notification,
            **updates
        )

    def set_cloned_settings(self, request, source_ad_group_source):
        source_ad_group_source_settings = source_ad_group_source.get_current_settings()
        self.settings.update(
            request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            daily_budget_cc=source_ad_group_source_settings.daily_budget_cc,
            cpc_cc=source_ad_group_source_settings.cpc_cc,
            cpm=source_ad_group_source_settings.cpm,
            state=source_ad_group_source_settings.state,
        )

    def get_tracking_ids(self):
        msid = self.source.tracking_slug or ""
        if self.source.source_type and self.source.source_type.type in [
            constants.SourceType.ZEMANTA,
            constants.SourceType.B1,
            constants.SourceType.OUTBRAIN,
        ]:
            msid = "{sourceDomain}"

        return "_z1_adgid={}&_z1_msid={}".format(self.ad_group_id, msid)

    def get_external_name(self, new_adgroup_name=None):
        account_name = self.ad_group.campaign.account.name
        campaign_name = self.ad_group.campaign.name
        if new_adgroup_name is None:
            ad_group_name = self.ad_group.name
        else:
            ad_group_name = new_adgroup_name
        ad_group_id = self.ad_group.id
        source_name = self.source.name
        return "ONE: {} / {} / {} / {} / {}".format(
            core.models.helpers.shorten_name(account_name),
            core.models.helpers.shorten_name(campaign_name),
            core.models.helpers.shorten_name(ad_group_name),
            ad_group_id,
            source_name,
        )

    def get_supply_dash_url(self):
        if not self.source.has_3rd_party_dashboard():
            return None

        return "{}?ad_group_id={}&source_id={}".format(
            reverse("supply_dash_redirect"), self.ad_group.id, self.source.id
        )

    def get_current_settings(self):
        return self.settings

    def migrate_to_bcm_v2(self, request, fee, margin):
        current_settings = self.get_current_settings()
        changes = {
            "daily_budget_cc": self._transform_daily_budget_cc(current_settings.daily_budget_cc, fee, margin),
            "cpc_cc": self._transform_cpc_cc(current_settings.cpc_cc, fee, margin),
        }

        self.settings.update(
            request=request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            skip_notification=True,
            **changes
        )

    def _transform_daily_budget_cc(self, daily_budget_cc, fee, margin):
        if not daily_budget_cc:
            return daily_budget_cc
        new_daily_budget_cc = core.features.bcm.calculations.apply_fee_and_margin(daily_budget_cc, fee, margin)
        return utils.numbers.round_decimal_ceiling(new_daily_budget_cc, places=0)

    def _transform_cpc_cc(self, cpc_cc, fee, margin):
        if not cpc_cc:
            return cpc_cc
        new_cpc_cc = core.features.bcm.calculations.apply_fee_and_margin(cpc_cc, fee, margin)
        return utils.numbers.round_decimal_half_down(new_cpc_cc, places=3)

    def save(self, request=None, *args, **kwargs):
        super(AdGroupSource, self).save(*args, **kwargs)

    def __str__(self):
        return "{} - {}".format(self.ad_group, self.source)
