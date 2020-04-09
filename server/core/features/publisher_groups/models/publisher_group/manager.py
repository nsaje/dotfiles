from django.db import models
from django.db import transaction

import core.common

from . import model


class PublisherGroupManager(models.Manager):
    @transaction.atomic
    def create(self, request, name, agency=None, account=None, default_include_subdomains=True, implicit=False):
        if not implicit:
            if agency is not None:
                core.common.entity_limits.enforce(model.PublisherGroup.objects.filter(agency=agency, implicit=False))
            elif account is not None:
                core.common.entity_limits.enforce(
                    model.PublisherGroup.objects.filter(account=account, implicit=False), account.id
                )

        publisher_group = model.PublisherGroup(
            name=name,
            agency=agency,
            account=account,
            default_include_subdomains=default_include_subdomains,
            implicit=implicit,
        )

        publisher_group.save(request)

        return publisher_group
