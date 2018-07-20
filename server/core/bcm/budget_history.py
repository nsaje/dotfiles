# -*- coding: utf-8 -*-

from django.db import models

import core.history


class BudgetHistory(core.history.HistoryModel):
    class Meta:
        app_label = "dash"

    budget = models.ForeignKey("BudgetLineItem", related_name="history")
