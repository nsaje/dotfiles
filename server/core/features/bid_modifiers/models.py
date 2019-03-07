from django.db import models

import core.models

from . import constants


class BidModifierQuerySet(models.QuerySet):
    def filter_by_user(self, user):
        if user.has_perm("zemauth.can_see_all_accounts"):
            return self
        return self.filter(
            models.Q(ad_group__campaign__account__users__id=user.id)
            | models.Q(ad_group__campaign__account__agency__users__id=user.id)
        ).distinct()


class PublisherBidModifierManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type=constants.BidModifierType.PUBLISHER)


class BidModifier(models.Model):
    class Meta:
        app_label = "dash"
        unique_together = ("type", "ad_group", "source_slug", "target")

    id = models.AutoField(primary_key=True)
    type = models.IntegerField(choices=constants.BidModifierType.get_choices())
    ad_group = models.ForeignKey(core.models.AdGroup, on_delete=models.PROTECT)
    source = models.ForeignKey(core.models.Source, on_delete=models.PROTECT, null=True, blank=True)
    source_slug = models.CharField(max_length=50, default="", blank=True)
    target = models.CharField(max_length=127, blank=False, null=False, verbose_name="Bid modifier target")
    modifier = models.FloatField(verbose_name="Bid modifier")
    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")

    objects = models.Manager.from_queryset(BidModifierQuerySet)()
    publisher_objects = PublisherBidModifierManager()
