# -*- coding: utf-8 -*-

from django.db import models
from dash import constants

import core.common
import core.entity


class PublisherBlacklist(models.Model):
    class Meta:
        app_label = 'dash'
        unique_together = (('name', 'everywhere', 'account',
                            'campaign', 'ad_group', 'source'), )

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127, blank=False,
                            null=False, verbose_name='Publisher name')
    everywhere = models.BooleanField(
        default=False, verbose_name='globally blacklisted')
    account = models.ForeignKey(
        'Account', null=True, related_name='account', on_delete=models.PROTECT)
    campaign = models.ForeignKey(
        'Campaign', null=True, related_name='campaign', on_delete=models.PROTECT)
    ad_group = models.ForeignKey(
        'AdGroup', null=True, related_name='ad_group', on_delete=models.PROTECT)
    source = models.ForeignKey('Source', null=True, on_delete=models.PROTECT)
    external_id = models.CharField(
        max_length=127, blank=True, null=True, verbose_name='External ID')

    status = models.IntegerField(
        default=constants.PublisherStatus.BLACKLISTED,
        choices=constants.PublisherStatus.get_choices()
    )

    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')

    def get_blacklist_level(self):
        level = constants.PublisherBlacklistLevel.ADGROUP
        if self.campaign_id is not None:
            level = constants.PublisherBlacklistLevel.CAMPAIGN
        elif self.account_id is not None:
            level = constants.PublisherBlacklistLevel.ACCOUNT
        elif self.everywhere:
            level = constants.PublisherBlacklistLevel.GLOBAL
        return level

    def fill_keys(self, ad_group, level):
        self.everywhere = False
        self.account = None
        self.campaign = None
        self.ad_group = None

        if level == constants.PublisherBlacklistLevel.GLOBAL:
            self.everywhere = True
        if level == constants.PublisherBlacklistLevel.ACCOUNT:
            self.account = ad_group.campaign.account
        if level == constants.PublisherBlacklistLevel.CAMPAIGN:
            self.campaign = ad_group.campaign
        if level == constants.PublisherBlacklistLevel.ADGROUP:
            self.ad_group = ad_group

    objects = core.common.QuerySetManager()

    class QuerySet(models.QuerySet):

        def filter_by_sources(self, sources):
            if not core.entity.helpers.should_filter_by_sources(sources):
                return self

            return self.filter(source__in=sources)
