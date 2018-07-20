# -*- coding: utf-8 -*-

from django.db import models

import core.history


class CreditHistory(core.history.HistoryModel):
    class Meta:
        app_label = "dash"

    credit = models.ForeignKey("CreditLineItem", related_name="history")
