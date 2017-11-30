# -*- coding: utf-8 -*-
import jsonfield
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models, transaction

from dash import constants, retargeting_helper

import core.bcm
import core.common
import core.entity
import core.history
import core.source

import utils.email_helper
import utils.exc
import utils.k1_helper
import utils.numbers

import validation

logger = logging.getLogger(__name__)


class AdGroupSourceManager(core.common.QuerySetManager):
    def _create(self, ad_group, source):
        default_settings = source.get_default_settings()
        ad_group_source = AdGroupSource(
            source=source,
            ad_group=ad_group,
            source_credentials=default_settings.credentials,
            can_manage_content_ads=source.can_manage_content_ads())
        ad_group_source.save(None)

        ad_group_source.settings = core.entity.settings.AdGroupSourceSettings(ad_group_source=ad_group_source)
        ad_group_source.settings.update(None)
        ad_group_source.settings_id = ad_group_source.settings.id
        ad_group_source.save(None)

        return ad_group_source

    @transaction.atomic
    def create(self, request, ad_group, source, write_history=True, k1_sync=True, **updates):
        ad_group_settings = ad_group.get_current_settings()

        if not ad_group.campaign.account.allowed_sources.filter(pk=source.id).exists():
            raise utils.exc.ValidationError(
                '{} media source can not be added to this account.'.format(source.name)
            )

        if AdGroupSource.objects.filter(source=source, ad_group=ad_group).exists():
            raise utils.exc.ValidationError(
                '{} media source for ad group {} already exists.'.format(source.name, ad_group.id))

        if not retargeting_helper.can_add_source_with_retargeting(source, ad_group_settings):
            raise utils.exc.ValidationError(
                '{} media source can not be added because it does not support retargeting.'.format(source.name))

        ad_group_source = self._create(ad_group, source)
        if write_history:
            ad_group.write_history_source_added(request, ad_group_source)

        ad_group_source.set_initial_settings(
            request,
            ad_group_settings,
            **updates
        )

        if settings.K1_CONSISTENCY_SYNC:
            # circular dependency
            from dash import api
            api.add_content_ad_sources(ad_group_source)

        if k1_sync:
            utils.k1_helper.update_ad_group(ad_group.id, msg='AdGroupSources.put')

        return ad_group_source

    @transaction.atomic
    def bulk_create_on_allowed_sources(self, request, ad_group, write_history=True, k1_sync=True):
        sources = ad_group.campaign.account.allowed_sources.all()
        added_ad_group_sources = []
        for source in sources:
            if source.maintenance:
                continue

            try:
                ad_group_source = self.create(request, ad_group, source, write_history=False, k1_sync=False)
                added_ad_group_sources.append(ad_group_source)
            except utils.exc.MissingDataError:
                # skips ad group sources creation without default sources
                logger.exception('Exception occurred on campaign with id %s', ad_group.campaign_id)
                continue

        if write_history:
            raise Exception("Can't write history at this stage")

        if k1_sync and added_ad_group_sources:
            utils.k1_helper.update_ad_group(ad_group.id, msg='AdGroupSources.put')

        return added_ad_group_sources

    @transaction.atomic
    def clone(self, request, ad_group, source_ad_group_source, write_history=True, k1_sync=True):
        ad_group_source = self._create(ad_group, source_ad_group_source.source)
        if write_history:
            ad_group.write_history_source_added(request, ad_group_source)

        ad_group_source.set_cloned_settings(None, source_ad_group_source)

        if settings.K1_CONSISTENCY_SYNC:
            from dash import api  # TODO circular dependency
            api.add_content_ad_sources(ad_group_source)

        if k1_sync:
            utils.k1_helper.update_ad_group(ad_group.id, msg='AdGroupSources.put')

        return ad_group_source

    @transaction.atomic
    def bulk_clone_on_allowed_sources(self, request, ad_group, source_ad_group, write_history=True, k1_sync=True):
        ad_group_sources = source_ad_group.adgroupsource_set.all().select_related('source')
        map_source_ad_group_sources = {x.source_id: x for x in ad_group_sources}

        added_ad_group_sources = []
        for source in ad_group.campaign.account.allowed_sources.all():
            if source.maintenance:
                continue

            try:
                if source.id in map_source_ad_group_sources:
                    ad_group_source = self.clone(
                        request, ad_group, map_source_ad_group_sources[source.id],
                        write_history=False, k1_sync=False)
                else:
                    continue

                added_ad_group_sources.append(ad_group_source)
            except utils.exc.MissingDataError:
                # skips ad group sources creation without default sources
                logger.exception('Exception occurred on campaign with id %s', ad_group.campaign_id)
                continue

        if write_history:
            raise Exception("Can't write history at this stage")

        if k1_sync and added_ad_group_sources:
            utils.k1_helper.update_ad_group(ad_group.id, msg='AdGroupSources.put')

        return added_ad_group_sources


class AdGroupSource(models.Model):
    class Meta:
        app_label = 'dash'

    source = models.ForeignKey('Source', on_delete=models.PROTECT)
    ad_group = models.ForeignKey('AdGroup', on_delete=models.PROTECT)

    source_credentials = models.ForeignKey(
        'SourceCredentials', null=True, on_delete=models.PROTECT)
    source_campaign_key = jsonfield.JSONField(blank=True, default={})

    last_successful_sync_dt = models.DateTimeField(blank=True, null=True)
    last_successful_reports_sync_dt = models.DateTimeField(
        blank=True, null=True)
    last_successful_status_sync_dt = models.DateTimeField(
        blank=True, null=True)
    can_manage_content_ads = models.BooleanField(
        null=False, blank=False, default=False)

    source_content_ad_id = models.CharField(
        max_length=100, null=True, blank=True)
    blockers = jsonfield.JSONField(blank=True, default={})

    settings = models.ForeignKey('AdGroupSourceSettings', null=True, blank=True, on_delete=models.PROTECT, related_name='latest_for_ad_group_source')

    objects = AdGroupSourceManager()

    class QuerySet(models.QuerySet):

        def filter_by_sources(self, sources):
            if not core.entity.helpers.should_filter_by_sources(sources):
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
                source_id__in=core.source.Source.objects.all().filter_can_manage_content_ads().values_list(
                    'id', flat=True))

    @transaction.atomic
    def update(self, request=None, k1_sync=True, system_user=None,
               skip_automation=False, skip_validation=False, skip_notification=False,
               **updates):
        result = {
            'autopilot_changed_sources_text': '',
        }

        ad_group_source_settings = self.get_current_settings()
        ad_group_settings = self.ad_group.get_current_settings()
        campaign_settings = self.ad_group.campaign.get_current_settings()

        if not skip_validation:
            validation.validate_ad_group_source_updates(
                self,
                updates,
                ad_group_settings,
                ad_group_source_settings,
            )

        if not skip_automation:
            validation.validate_ad_group_source_campaign_stop(
                self,
                updates,
                campaign_settings,
                ad_group_settings,
                ad_group_source_settings,
            )

        old_settings = self.settings.get_settings_dict()

        changes = self.settings.get_changes(updates)
        if not changes:
            return result

        if not request:
            updates['system_user'] = system_user
        self.settings.update(request, **updates)

        from automation import autopilot_plus
        if not skip_automation and\
                ad_group_settings.autopilot_state == constants.AdGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET and\
                'state' in updates:
            changed_sources = autopilot_plus.initialize_budget_autopilot_on_ad_group(ad_group_settings, send_mail=False)
            result['autopilot_changed_sources_text'] = ', '.join(
                [s.source.name if s != constants.SourceAllRTB else constants.SourceAllRTB.NAME
                    for s in changed_sources])

        if not skip_notification:
            self._notify_ad_group_source_settings_changed(request, changes, old_settings)

        if k1_sync:
            utils.k1_helper.update_ad_group(self.ad_group.pk, 'AdGroupSource.update')

        return result

    def set_initial_settings(self, request, ad_group_settings, **updates):
        from dash.views import helpers

        if 'cpc_cc' not in updates:
            updates['cpc_cc'] = self.source.default_cpc_cc
            if ad_group_settings.is_mobile_only():
                updates['cpc_cc'] = self.source.default_mobile_cpc_cc
            if (ad_group_settings.b1_sources_group_enabled and
                    ad_group_settings.b1_sources_group_cpc_cc > 0.0 and
                    self.source.source_type.type == constants.SourceType.B1):
                updates['cpc_cc'] = ad_group_settings.b1_sources_group_cpc_cc
            if ad_group_settings.cpc_cc:
                updates['cpc_cc'] = min(ad_group_settings.cpc_cc, updates['cpc_cc'])
        if 'state' not in updates:
            if helpers.get_source_initial_state(self):
                updates['state'] = constants.AdGroupSourceSettingsState.ACTIVE
            else:
                updates['state'] = constants.AdGroupSourceSettingsState.INACTIVE
        if 'daily_budget_cc' not in updates:
            updates['daily_budget_cc'] = self.source.default_daily_budget_cc

        enabling_autopilot_sources_allowed = helpers.enabling_autopilot_sources_allowed(
            ad_group_settings,
            [self],
        )
        if not enabling_autopilot_sources_allowed:
            updates['state'] = constants.AdGroupSourceSettingsState.INACTIVE

        self.update(
            request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            **updates
        )

    def set_cloned_settings(self, request, source_ad_group_source):
        source_ad_group_source_settings = source_ad_group_source.get_current_settings()
        self.update(
            request,
            k1_sync=False,
            skip_automation=True,
            skip_validation=True,
            daily_budget_cc=source_ad_group_source_settings.daily_budget_cc,
            cpc_cc=source_ad_group_source_settings.cpc_cc,
            state=source_ad_group_source_settings.state,
        )

    def get_tracking_ids(self):
        msid = self.source.tracking_slug or ''
        if self.source.source_type and\
           self.source.source_type.type in [
                constants.SourceType.ZEMANTA, constants.SourceType.B1, constants.SourceType.OUTBRAIN]:
            msid = '{sourceDomain}'

        return '_z1_adgid={}&_z1_msid={}'.format(self.ad_group_id, msid)

    def get_external_name(self, new_adgroup_name=None):
        account_name = self.ad_group.campaign.account.name
        campaign_name = self.ad_group.campaign.name
        if new_adgroup_name is None:
            ad_group_name = self.ad_group.name
        else:
            ad_group_name = new_adgroup_name
        ad_group_id = self.ad_group.id
        source_name = self.source.name
        return u'ONE: {} / {} / {} / {} / {}'.format(
            core.entity.helpers.shorten_name(account_name),
            core.entity.helpers.shorten_name(campaign_name),
            core.entity.helpers.shorten_name(ad_group_name),
            ad_group_id,
            source_name
        )

    def get_supply_dash_url(self):
        if not self.source.has_3rd_party_dashboard():
            return None

        return '{}?ad_group_id={}&source_id={}'.format(
            reverse('supply_dash_redirect'),
            self.ad_group.id,
            self.source.id
        )

    def get_current_settings(self):
        return self.settings

    def migrate_to_bcm_v2(self, request, fee, margin):
        current_settings = self.get_current_settings()
        changes = {
            'daily_budget_cc': self._transform_daily_budget_cc(current_settings.daily_budget_cc, fee, margin),
            'cpc_cc': self._transform_cpc_cc(current_settings.cpc_cc, fee, margin),
        }

        self.update(
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
        new_daily_budget_cc = core.bcm.calculations.apply_fee_and_margin(
            daily_budget_cc, fee, margin
        )
        return utils.numbers.round_decimal_ceiling(new_daily_budget_cc, places=0)

    def _transform_cpc_cc(self, cpc_cc, fee, margin):
        if not cpc_cc:
            return cpc_cc
        new_cpc_cc = core.bcm.calculations.apply_fee_and_margin(
            cpc_cc, fee, margin
        )
        return utils.numbers.round_decimal_half_down(new_cpc_cc, places=3)

    def save(self, request=None, *args, **kwargs):
        super(AdGroupSource, self).save(*args, **kwargs)

    def __unicode__(self):
        return u'{} - {}'.format(self.ad_group, self.source)

    def __str__(self):
        return unicode(self).encode('ascii', 'ignore')

    def _notify_ad_group_source_settings_changed(self, request, changes, old_settings):
        if not request:
            return

        changes_text_parts = []
        for key, val in changes.items():
            if val is None:
                continue
            field = self.settings.get_human_prop_name(key)
            val = self.settings.get_human_value(key, val)
            source_name = self.source.name
            old_val = old_settings[key]
            if old_val is None:
                text = '%s %s set to %s' % (source_name, field, val)
            else:
                old_val = self.settings.get_human_value(key, old_val)
                text = '%s %s set from %s to %s' % (source_name, field, old_val, val)
            changes_text_parts.append(text)

        utils.email_helper.send_ad_group_notification_email(
            self.ad_group, request, '\n'.join(changes_text_parts))
