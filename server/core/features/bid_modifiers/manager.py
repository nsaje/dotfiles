from django.db import models

from . import constants


class PublisherBidModifierManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(type=constants.BidModifierType.PUBLISHER)
