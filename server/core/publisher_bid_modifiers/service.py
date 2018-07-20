import numbers

from django.db import transaction

from . import exceptions
from .publisher_bid_modifier import PublisherBidModifier

MODIFIER_MAX = 11.0
MODIFIER_MIN = 0.0


def get(ad_group):
    return [
        {"publisher": item.publisher, "source": item.source, "modifier": item.modifier}
        for item in PublisherBidModifier.objects.filter(ad_group=ad_group).select_related("source").order_by("pk")
    ]


@transaction.atomic
def set(ad_group, publisher, source, modifier):
    if not modifier:
        _delete(ad_group, source, publisher)
        return

    if not isinstance(modifier, numbers.Number) or not MODIFIER_MIN <= modifier <= MODIFIER_MAX:
        raise exceptions.BidModifierInvalid

    _update_or_create(ad_group, source, publisher, modifier)


def _delete(ad_group, source, publisher):
    PublisherBidModifier.objects.filter(ad_group=ad_group, source=source, publisher=publisher).delete()


def _update_or_create(ad_group, source, publisher, modifier):
    PublisherBidModifier.objects.update_or_create(
        defaults={"modifier": modifier}, ad_group=ad_group, source=source, publisher=publisher
    )
