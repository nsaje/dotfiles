# -*- coding: utf-8 -*-
import datetime

from django.conf import settings
from django.db import models

import core.common
import core.models.helpers
from dash import constants


class CustomHack(models.Model):
    id = models.AutoField(primary_key=True)
    agency = models.ForeignKey("Agency", null=True, blank=True, related_name="hacks", on_delete=models.PROTECT)
    account = models.ForeignKey("Account", null=True, blank=True, related_name="hacks", on_delete=models.PROTECT)
    campaign = models.ForeignKey("Campaign", null=True, blank=True, related_name="hacks", on_delete=models.PROTECT)
    ad_group = models.ForeignKey("AdGroup", null=True, blank=True, related_name="hacks", on_delete=models.PROTECT)
    source = models.ForeignKey("Source", null=True, blank=True, related_name="hacks", on_delete=models.PROTECT)
    rtb_only = models.BooleanField(default=False)

    summary = models.CharField(null=True, blank=True, max_length=255)
    details = models.TextField(null=True, blank=True)
    service = models.CharField(default=constants.Service.Z1, choices=constants.Service.get_choices(), max_length=255)
    trello_ticket_url = models.CharField(null=True, blank=True, max_length=255)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.PROTECT
    )

    removed_dt = models.DateTimeField(null=True, blank=True, verbose_name="Removed at")

    confirmed_dt = models.DateTimeField(null=True, blank=True, verbose_name="Confirmed at")
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name="+", on_delete=models.PROTECT
    )

    objects = core.common.QuerySetManager()

    def save(self, request=None, *args, **kwargs):
        if self.pk is None and request:
            self.created_by = request.user
        super(CustomHack, self).save(*args, **kwargs)

    def get_level(self):
        return (
            self.agency
            and "Agency"
            or self.account
            and "Account"
            or self.campaign
            and "Campaign"
            or self.ad_group
            and "Ad group"
            or "Global"
        )

    def get_entity(self):
        return self.agency or self.account or self.campaign or self.ad_group

    def is_global(self):
        return not self.get_entity()

    def __str__(self):
        desc = "{level} level hack"
        if self.source:
            desc += " on source {source}"
        if self.rtb_only:
            desc += " on all RTB sources"
        desc += ": {summary}"
        return desc.format(level=self.get_level(), source=self.source, summary=self.summary)

    class QuerySet(models.QuerySet):
        def filter_applied(self, source=None, **levels):
            ad_group = levels.get("ad_group")
            campaign, account, agency = core.models.helpers.generate_parents(**levels)
            rules = models.Q(agency=None, account=None, campaign=None, ad_group=None)
            if agency:
                rules |= models.Q(agency=agency)
            if account:
                rules |= models.Q(account=account)
            if campaign:
                rules |= models.Q(campaign=campaign)
            if ad_group:
                rules |= models.Q(ad_group=ad_group)
            queryset = self.filter(rules)
            if source:
                queryset = queryset.filter(models.Q(source=source) | models.Q(source=None))
            return queryset

        def filter_active(self, is_active):
            now = datetime.datetime.now()
            if is_active:
                return self.filter(models.Q(removed_dt__isnull=True) | models.Q(removed_dt__gt=now))
            else:
                return self.filter(removed_dt__lte=now)

        def to_dict_list(self):
            return [
                {
                    "summary": obj.summary,
                    "details": obj.details,
                    "level": obj.get_level(),
                    "source": obj.source and obj.source.name or obj.rtb_only and "RTB" or None,
                    "confirmed": obj.confirmed_by is not None,
                }
                for obj in self
            ]
