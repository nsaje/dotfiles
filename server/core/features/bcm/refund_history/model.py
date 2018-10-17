from django.db import models

import core.features.history


class RefundHistory(core.features.history.HistoryModel):
    class Meta:
        app_label = "dash"

    refund = models.ForeignKey("RefundLineItem", related_name="history", on_delete=models.PROTECT)
