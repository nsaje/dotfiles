# -*- coding: utf-8 -*-
import jsonfield
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import models

from dash import constants
from utils import exc

import core.common
import core.entity
import core.history
import core.source


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

    objects = core.common.QuerySetManager()

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
            raise exc.BaseError(
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
