# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import Q

import core.common
import core.pixels
from dash import constants
from utils import exc
from utils import k1_helper
from utils import redirector_helper

from . import audience_rule


class AudienceManager(core.common.BaseManager):
    def create(self, request, name, pixel, ttl, prefill_days, rules):
        audience = None
        refererRules = (constants.AudienceRuleType.CONTAINS, constants.AudienceRuleType.STARTS_WITH)
        with transaction.atomic():
            audience = Audience(
                name=name,
                pixel=pixel,
                ttl=ttl,
                prefill_days=ttl,  # use ttl value for prefill until it gets its own UI component
                created_by=request.user,
            )

            audience._save()
            audience.add_to_history(
                request.user,
                constants.HistoryActionType.AUDIENCE_CREATE,
                'Created audience "{}".'.format(audience.name),
            )

            for rule in rules:
                value = rule["value"] or ""
                if rule["type"] in refererRules:
                    value = ",".join([x.strip() for x in value.split(",") if x])

                rule = audience_rule.AudienceRule(audience=audience, type=rule["type"], value=value)
                rule.save()

            redirector_helper.upsert_audience(audience)

        k1_helper.update_account(pixel.account_id, msg="audience.create")

        return audience


class Audience(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=127, editable=True, blank=False, null=False)
    pixel = models.ForeignKey(core.pixels.ConversionPixel, on_delete=models.PROTECT)
    archived = models.BooleanField(default=False)
    ttl = models.PositiveSmallIntegerField()
    prefill_days = models.PositiveSmallIntegerField(default=0)
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="+", on_delete=models.PROTECT)

    objects = AudienceManager()

    def _save(self, *args, **kwargs):
        """Proxy method for the parent method, which must be used in methods"""
        super(Audience, self).save(args, kwargs)

    def save(self, *args, **kwargs):
        raise exc.ForbiddenError("Using directly the save method is prohibited.")

    def add_to_history(self, user, action_type, history_changes_text):
        self.pixel.account.write_history(history_changes_text, changes=None, action_type=action_type, user=user)

    class Meta:
        app_label = "dash"

    def get_ad_groups_using_audience(self):
        #  Circular import workaround
        import core.models.ad_group

        ad_groups_using_audience = core.models.ad_group.AdGroup.objects.filter(
            campaign__account_id=self.pixel.account_id
        ).filter(
            Q(settings__audience_targeting__contains=self.id)
            | Q(settings__exclusion_audience_targeting__contains=self.id)
        )
        return ad_groups_using_audience

    def can_archive(self):
        if self.get_ad_groups_using_audience():
            return False
        return True

    @transaction.atomic
    def update(self, request, name=None, archived=None):
        if self.archived is False and archived is True:
            if not self.can_archive():
                raise exc.ValidationError(
                    errors="Audience '{name}' is currently targeted on ad groups {adgroups}.".format(
                        name=self.name, adgroups=", ".join([ad.name for ad in self.get_ad_groups_using_audience()])
                    )
                )
            self.archived = True
            self.add_to_history(
                request.user, constants.HistoryActionType.AUDIENCE_ARCHIVE, 'Archived audience "{}".'.format(self.name)
            )

        if self.archived is True and archived is False:
            self.archived = False
            self.add_to_history(
                request.user, constants.HistoryActionType.AUDIENCE_RESTORE, 'Restored audience "{}".'.format(self.name)
            )

        if name and name != self.name:
            old_name = self.name
            self.name = name
            self.add_to_history(
                request.user,
                constants.HistoryActionType.AUDIENCE_UPDATE,
                'Changed audience name from "{}" to "{}".'.format(old_name, self.name),
            )
        self._save()

        redirector_helper.upsert_audience(self)
        k1_helper.update_account(self.pixel.account_id, msg="audience.update")
