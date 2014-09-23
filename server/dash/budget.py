
from django.db import transaction

import dash.models
import reports.api


class CompositeBudget(object):

    def get_components(self):
        raise NotImplementedError

    def get_total(self):
        return sum(c.get_total() for c in self.get_components())

    def get_spend(self):
        return sum(c.get_total() for c in self.get_components())


class GlobalBudget(CompositeBudget):

    def get_components(self):
        for account in dash.models.Accounts.objects.all():
            yield AccountBudget(account)


class AccountBudget(CompositeBudget):

    def __init__(self, account):
        self.account = account
        try:
            self.cbs_latest = dash.models.CampaignBudgetSettings.objects.filter(campaign=self.campaign).latest()
        except dash.models.CampaignBudgetSettings.DoesNotExist:
            self.cbs_latest = None

    def get_components(self):
        for campaign in dash.model.Campaign.objects.filter(account=self.account):
            yield CampaignBudget(campaign)


class CampaignBudget(object):

    def __init__(self, campaign):
        self.campaign = campaign

    def get_total(self):
        if self.cbs_latest is None:
            return 0
        else:
            return self.cbs_latest.total

    def get_spend(self):
        reports.api.query(start_date=None, end_date=None, campaign=self.campaign)

    def edit(self, allocate_amount, revoke_amount, user, latest_id):
        if not self._can_edit(user):
            return

        with transaction.atomic():
            cbs_latest = dash.models.CampaignBudgetSettings.objects.filter(campaign=self.campaign).latest()
            if cbs.id != latest_id:
                # somebody already edited budget settings in the meantime
                raise 
            cbs_new = dash.models.CampaignBudgetSettings(
                campaign=self.campaign,
                allocate=allocate_amount,
                revoke=revoke_amount,
                total=cbs_latest.total + allocate_amount - revoke_amount,
                note=note,
                created_by=user
            )
            cbs_new.save()

    def get_history(self):
        pass

    def get_latest_id(self):
        if self.cbs_latest is not None:
            return self.cbs_latest.id
        else:
            return None

    def _can_edit(self, user):
        return self.campaign in dash.models.Campaign.objects.get_for_user(user)

