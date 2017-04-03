# -*- coding: utf-8 -*-
from django.conf import settings
from django.db import models

import core.pixels


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
