from django.db import transaction


class DirectDealConnectionMixin(object):
    @property
    def is_global(self):
        if not any([self.adgroup, self.agency, self.account, self.campaign]):
            return True
        return False

    @property
    def level(self):
        return (
            self.agency
            and "Agency"
            or self.account
            and "Account"
            or self.campaign
            and "Campaign"
            or self.adgroup
            and "Ad group"
            or "Global"
        )

    @transaction.atomic
    def save(self, request=None, *args, **kwargs):
        if self.is_global:
            self.exclusive = False

        if request and not request.user.is_anonymous:
            if self.pk is None:
                self.created_by = request.user
            self.modified_by = request.user

        self.full_clean()
        super().save(*args, **kwargs)
