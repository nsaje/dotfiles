# -*- coding: utf-8 -*-

from django.db import models

from dash import constants

from . import instance


class FacebookAccount(instance.FacebookAccountMixin, models.Model):
    class Meta:
        app_label = "dash"

    account = models.OneToOneField("Account", primary_key=True, on_delete=models.CASCADE)
    ad_account_id = models.CharField(max_length=127, blank=True, null=True)
    page_url = models.CharField(max_length=255, blank=True, null=True)
    page_id = models.CharField(max_length=127, blank=True, null=True)
    status = models.IntegerField(
        default=constants.FacebookPageRequestType.EMPTY, choices=constants.FacebookPageRequestType.get_choices()
    )
