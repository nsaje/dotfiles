# -*- coding: utf-8 -*-
import jsonfield
import logging
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models, transaction

from dash import constants

import core.common
import core.entity
import core.history
import core.source

import utils.exc
import utils.k1_helper


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
        return ad_group_source

    @transaction.atomic
    def create(self, request, ad_group, source, write_history=True, k1_sync=True):
        ad_group_source = self._create(ad_group, source)
        if write_history:
            ad_group.write_history_source_added(request, ad_group_source)

        ad_group_settings = ad_group.get_current_settings()

        # circular dependency
        from dash.views import helpers
        ad_group_source.set_initial_settings(
            None,
            active=helpers.get_source_initial_state(ad_group_source),  # TODO move this
            mobile_only=ad_group_settings.is_mobile_only())

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
            except utils.exc.MissingDataError as e:
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

        from dash.views import helpers  # TODO circular dependency
        ad_group_source.set_cloned_settings(None, source_ad_group_source,
                                            active=helpers.get_source_initial_state(ad_group_source))

        if settings.K1_CONSISTENCY_SYNC:
            from dash import api  # TODO circular dependency
            api.add_content_ad_sources(ad_group_source)

        if k1_sync:
            utils.k1_helper.update_ad_group(ad_group.id, msg='AdGroupSources.put')

        return ad_group_source

    @transaction.atomic
    def bulk_clone_on_allowed_sources(self, request, ad_group, source_ad_group, write_history=True, k1_sync=True):
        map_source_ad_group_sources = {x.source_id: x for x in source_ad_group.adgroupsource_set.all()}

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
                    ad_group_source = self.create(request, ad_group, source, write_history=False, k1_sync=False)

                added_ad_group_sources.append(ad_group_source)
            except utils.exc.MissingDataError as e:
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
            latest_ags_settings = core.entity.settings.AdGroupSourceSettings.objects.\
                filter(ad_group_source__in=self).\
                group_current_settings()
            active_ags_ids = core.entity.settings.AdGroupSourceSettings.objects.\
                filter(id__in=latest_ags_settings).\
                filter(state=constants.AdGroupSourceSettingsState.ACTIVE).\
                values_list('ad_group_source_id', flat=True)
            return self.filter(id__in=active_ags_ids)

        def filter_can_manage_content_ads(self):
            return self.filter(
                can_manage_content_ads=True,
                source_id__in=core.source.Source.objects.all().filter_can_manage_content_ads().values_list(
                    'id', flat=True))

    def set_initial_settings(self, request, mobile_only=False, active=False, max_cpc=None):
        cpc_cc = self.source.default_cpc_cc
        if mobile_only:
            cpc_cc = self.source.default_mobile_cpc_cc
        ag_settings = self.ad_group.get_current_settings()
        if (ag_settings.b1_sources_group_enabled and
                ag_settings.b1_sources_group_cpc_cc > 0.0 and
                self.source.source_type.type == constants.SourceType.B1):
            cpc_cc = ag_settings.b1_sources_group_cpc_cc
        if max_cpc:
            cpc_cc = min(max_cpc, cpc_cc)

        resource = {
            'daily_budget_cc': self.source.default_daily_budget_cc,
            'cpc_cc': cpc_cc,
            'state': (constants.AdGroupSourceSettingsState.ACTIVE if active
                      else constants.AdGroupSourceSettingsState.INACTIVE),
        }

        from dash import api  # TODO circular import
        api.set_ad_group_source_settings(self, resource, request, ping_k1=False)

    def set_cloned_settings(self, request, source_ad_group_source, active=False):
        source_ad_group_source_settings = source_ad_group_source.get_current_settings()
        resource = {
            'daily_budget_cc': source_ad_group_source_settings.daily_budget_cc,
            'cpc_cc': source_ad_group_source_settings.cpc_cc,
            'state': (constants.AdGroupSourceSettingsState.ACTIVE if active
                      else constants.AdGroupSourceSettingsState.INACTIVE),
        }

        from dash import api  # TODO circular import
        api.set_ad_group_source_settings(self, resource, request, ping_k1=False)

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

    def get_latest_state(self):
        try:
            return core.entity.settings.AdGroupSourceState.objects.filter(
                ad_group_source=self
            ).latest()
        except core.entity.settings.AdGroupSourceState.DoesNotExist:
            return None

    def get_current_settings(self):
        current_settings = self.get_current_settings_or_none()
        return current_settings if current_settings else \
            core.entity.settings.AdGroupSourceSettings(ad_group_source=self)

    def get_current_settings_or_none(self):
        if not self.pk:
            raise utils.exc.BaseError(
                'Ad group source settings can\'t be fetched because ad group source hasn\'t been saved yet.'
            )

        try:
            return core.entity.settings.AdGroupSourceSettings.objects\
                .filter(ad_group_source_id=self.pk)\
                .latest('created_dt')
        except ObjectDoesNotExist:
            return None

    def save(self, request=None, *args, **kwargs):
        super(AdGroupSource, self).save(*args, **kwargs)
        if not core.entity.settings.AdGroupSourceSettings.objects.filter(ad_group_source=self).exists():
            settings = core.entity.settings.AdGroupSourceSettings(ad_group_source=self)
            settings.save(request)

    def __unicode__(self):
        return u'{} - {}'.format(self.ad_group, self.source)

    def __str__(self):
        return unicode(self).encode('ascii', 'ignore')
