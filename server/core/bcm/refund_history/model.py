from django.db import models

import core.history


class RefundHistory(core.history.HistoryModel):
    class Meta:
        app_label = "dash"

    refund = models.ForeignKey("RefundLineItem", related_name="history")
