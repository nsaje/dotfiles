# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models
from django.db import transaction

import core.common
import core.pixels
from dash import constants
from utils import k1_helper
from utils import redirector_helper

from . import audience_rule


class AudienceManager(core.common.BaseManager):
    def create(self, request, name, pixel, ttl, rules):
        audience = None
        refererRules = (constants.AudienceRuleType.CONTAINS, constants.AudienceRuleType.STARTS_WITH)
        with transaction.atomic():
            audience = Audience(
                name=name,
                pixel=pixel,
                ttl=ttl,
            )
            audience.save(
                request,
                constants.HistoryActionType.AUDIENCE_CREATE,
                'Created audience "{}".'.format(audience.name)
            )

            for rule in rules:
                value = rule['value'] or ''
                if rule['type'] in refererRules:
                    value = ','.join([x.strip() for x in value.split(',') if x])

                rule = audience_rule.AudienceRule(
                    audience=audience,
                    type=rule['type'],
                    value=value,
                )
                rule.save()

            redirector_helper.upsert_audience(audience)

        k1_helper.update_account(pixel.account_id, msg="audience.create")

        return audience


class Audience(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=127,
        editable=True,
        blank=False,
        null=False
    )
    pixel = models.ForeignKey(core.pixels.ConversionPixel, on_delete=models.PROTECT)
    archived = models.BooleanField(default=False)
    ttl = models.PositiveSmallIntegerField()
    created_dt = models.DateTimeField(
        auto_now_add=True, verbose_name='Created at')
    modified_dt = models.DateTimeField(
        auto_now=True, verbose_name='Modified at')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='+', on_delete=models.PROTECT)

    objects = AudienceManager()

    def save(self,
             request,
             action_type=None,
             changes_text=None,
             *args, **kwargs):
        if self.pk is None:
            self.created_by = request.user
        super(Audience, self).save(*args, **kwargs)
        self.add_to_history(request and request.user,
                            action_type, changes_text)

    def add_to_history(self, user, action_type, history_changes_text):
        self.pixel.account.write_history(
            history_changes_text,
            changes=None,
            action_type=action_type,
            user=user,
        )

    class Meta:
        app_label = 'dash'
