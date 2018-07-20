from django.db import models

import core.entity
import core.source


class RealTimeDataHistory(models.Model):
    ad_group = models.ForeignKey(core.entity.AdGroup)
    source = models.ForeignKey(core.source.Source)
    date = models.DateField(db_index=True)
    etfm_spend = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at", db_index=True)

    def __str__(self):
        return "${} (ad group: {} ({}), source: {}, date: {}, created dt: {})".format(
            self.etfm_spend, self.ad_group.name, self.ad_group.id, self.source.name, self.date, self.created_dt
        )


class RealTimeCampaignDataHistory(models.Model):
    campaign = models.ForeignKey(core.entity.Campaign)
    date = models.DateField(db_index=True)
    etfm_spend = models.DecimalField(max_digits=14, decimal_places=4, default=0)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at", db_index=True)

    def __str__(self):
        return "${} (campaign: {} ({}), date: {}, created dt: {})".format(
            self.etfm_spend, self.campaign.name, self.campaign.id, self.date, self.created_dt
        )
