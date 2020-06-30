from django.db import models


class EntityPermissionQuerySet(models.QuerySet):
    def filter_by_agency(self, agency):
        return self.filter(agency=agency)

    def filter_by_account(self, account):
        entity_permission_qs = self.filter(account=account)
        if account.agency is not None:
            entity_permission_qs |= self.filter_by_agency(account.agency)
        return entity_permission_qs

    def filter_by_accounts(self, accounts):
        return self.filter(account__in=accounts)

    def filter_by_campaign(self, campaign):
        return self.filter(models.Q(agency__account__campaign=campaign) | models.Q(account__campaign=campaign))

    def filter_by_adgroup(self, adgroup):
        return self.filter(
            models.Q(agency__account__campaign__adgroup=adgroup) | models.Q(account__campaign__adgroup=adgroup)
        )

    def filter_by_user(self, user):
        return self.filter(user=user)

    def filter_by_agency_or_its_accounts(self, agency_id):
        if not agency_id:
            return self
        return self.filter(models.Q(agency_id=agency_id) | models.Q(account__agency_id=agency_id))

    def filter_by_internal(self):
        return self.filter(models.Q(agency=None) & models.Q(account=None))

    def delete(self):
        for item in self:
            item.user.invalidate_entity_permission_cache()
        super().delete()
