from django.db import transaction

import dash.constants


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
        if self.pk is None:
            self.write_create_history(request)
        super().save(*args, **kwargs)

    def delete(self, request=None, using=None, keep_parents=False):
        self.write_delete_history(request)
        super().delete(using=using, keep_parents=keep_parents)

    def write_create_history(self, request=None):
        changes_text = "Added deal ({}{}/ {})".format(
            "{}/ ".format(self.deal.name) if self.deal.name is not None else "",
            self.deal.source.name,
            self.deal.deal_id,
        )
        action_type = dash.constants.HistoryActionType.DEAL_CONNECTION_CREATE
        user = request.user if request and not request.user.is_anonymous else None
        self.write_history(changes_text, action_type, user)

    def write_delete_history(self, request=None):
        changes_text = "Removed deal ({}{}/ {})".format(
            "{}/ ".format(self.deal.name) if self.deal.name is not None else "",
            self.deal.source.name,
            self.deal.deal_id,
        )
        action_type = dash.constants.HistoryActionType.DEAL_CONNECTION_DELETE
        user = request.user if request and not request.user.is_anonymous else None
        self.write_history(changes_text, action_type, user)

    def write_history(self, changes_text, action_type, user=None):
        if self.agency:
            self.agency.write_history(changes_text, action_type=action_type, user=user)
        elif self.account:
            self.account.write_history(changes_text, action_type=action_type, user=user)
        elif self.campaign:
            self.campaign.write_history(changes_text, action_type=action_type, user=user)
        elif self.adgroup:
            self.adgroup.write_history(changes_text, action_type=action_type, user=user)
