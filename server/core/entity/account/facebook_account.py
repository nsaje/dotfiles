# -*- coding: utf-8 -*-

from django.db import models

from dash import constants


class FacebookAccount(models.Model):
    class Meta:
        app_label = 'dash'

    account = models.OneToOneField('Account', primary_key=True)
    ad_account_id = models.CharField(max_length=127, blank=True, null=True)
    page_url = models.CharField(max_length=255, blank=True, null=True)
    page_id = models.CharField(max_length=127, blank=True, null=True)
    status = models.IntegerField(
        default=constants.FacebookPageRequestType.EMPTY,
        choices=constants.FacebookPageRequestType.get_choices()
    )

    def __str__(self):
        return self.account.name
