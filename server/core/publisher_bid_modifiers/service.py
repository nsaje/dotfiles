import numbers

from django.db import transaction

from . import exceptions
from publisher_bid_modifier import PublisherBidModifier

MODIFIER_MAX = 7.0
MODIFIER_MIN = 0.01


@transaction.atomic
def set(ad_group, source, publisher, modifier):
    if not modifier or modifier == 1.0:
        _delete(ad_group, source, publisher)
        return

    if not isinstance(modifier, numbers.Number) or not MODIFIER_MIN <= modifier <= MODIFIER_MAX:
        raise exceptions.BidModifierInvalid

    _update_or_create(ad_group, source, publisher, modifier)


def _delete(ad_group, source, publisher):
    PublisherBidModifier.objects.filter(
        ad_group=ad_group,
        source=source,
        publisher=publisher
    ).delete()


def _update_or_create(ad_group, source, publisher, modifier):
    PublisherBidModifier.objects.update_or_create(
        defaults={'modifier': modifier},
        ad_group=ad_group,
        source=source,
        publisher=publisher
    )
