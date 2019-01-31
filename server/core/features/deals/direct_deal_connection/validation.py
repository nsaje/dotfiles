from . import exceptions


class DirectDealsConnectionMixin(object):
    def _validate_exclusive(self):
        if self.exclusive and self.is_global:
            raise exceptions.CannotSetExclusiveAndGlobal(
                "Exclusive flag can be set only in combination with an entity, not on an exclusive deal."
            )

    def _validate_entities(self):
        entities = []
        if self.agency:
            entities.append(self.agency.name)
        if self.account:
            entities.append(self.account.name)
        if self.campaign:
            entities.append(self.campaign.name)
        if self.adgroup:
            entities.append(self.adgroup.name)

        if len(entities) > 1:
            msg = "Configuring {} at the same time is not allowed.".format(" and ".join(entities))
            raise exceptions.CannotSetMultipleEntities(msg)

    def clean(self):
        self._validate_entities()
        self._validate_exclusive()
