# -*- coding: utf-8 -*-

from django.db import models

import core.features.history


class CreditHistory(core.features.history.HistoryModel):
    class Meta:
        app_label = "dash"

    credit = models.ForeignKey("CreditLineItem", related_name="history")
