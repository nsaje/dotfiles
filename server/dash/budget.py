import datetime
import logging

from django.db import transaction

import dash.models
import reports.api

logger = logging.getLogger(__name__)


class CompositeBudget(object):

    def get_components(self):
        raise NotImplementedError

    def get_total(self):
        return sum(c.get_total() for c in self.get_components())

    def get_spend(self):
        return sum(c.get_total() for c in self.get_components())


class GlobalBudget(CompositeBudget):

    def get_components(self):
        for account in dash.models.Account.objects.all():
            yield AccountBudget(account)

    def get_spend(self):
        start_date = datetime.date(datetime.MINYEAR, 1, 1)
        end_date = datetime.datetime.utcnow().date()
        r = reports.api.query(start_date=start_date, end_date=end_date)
        return r.get('cost') or 0

    def get_total_by_account(self):
        qs = dash.models.CampaignBudgetSettings.objects \
            .select_related('campaign__account') \
            .distinct('campaign').order_by('campaign', '-created_dt') \
            .values('campaign__account', 'total')
        total_budget = {}
        for row in qs:
            if row['campaign__account'] not in total_budget:
                total_budget[row['campaign__account']] = 0
            total_budget[row['campaign__account']] += float(row['total'])
        return total_budget

    def get_spend_by_account(self):
        start_date = datetime.date(datetime.MINYEAR, 1, 1)
        end_date = datetime.datetime.utcnow().date()
        rs = reports.api.query(
            start_date=start_date,
            end_date=end_date,
            breakdown=['account']
        )
        result = {r['account']:(r.get('cost') or 0) for r in rs}
        return result


class AccountBudget(CompositeBudget):

    def __init__(self, account):
        self.account = account

    def get_components(self):
        for campaign in dash.models.Campaign.objects.filter(account=self.account):
            yield CampaignBudget(campaign)

    def get_spend(self):
        start_date = datetime.date(datetime.MINYEAR, 1, 1)
        end_date = datetime.datetime.utcnow().date()
        r = reports.api.query(start_date=start_date, end_date=end_date, account=self.account)
        return r.get('cost') or 0


class CampaignBudget(object):

    def __init__(self, campaign):
        self.campaign = campaign

    def get_total(self):
        cbs_latest = self.campaign.get_current_budget_settings()
        return float(cbs_latest.total) if cbs_latest is not None else 0

    def get_spend(self, until_date=None):
        start_date = datetime.date(datetime.MINYEAR, 1, 1)
        end_date = until_date or datetime.datetime.utcnow().date()
        r = reports.api.query(start_date=start_date, end_date=end_date, campaign=self.campaign)
        return r.get('cost') or 0

    def edit(self, allocate_amount, revoke_amount, request, comment=''):
        if not allocate_amount and not revoke_amount and not comment:
            # nothing to change
            return

        if allocate_amount > 0 or revoke_amount > 0:
            parts = []
            if allocate_amount:
                parts.append('Allocated $%.2f to the campaign' % allocate_amount)
            if revoke_amount:
                parts.append('Revoked $%.2f from the campaign' % revoke_amount)
            comment = ' and '.join(parts) + '.'

        logger.info(
            'Budget change: allocate=%s, revoke=%s, user=%s, comment=%s',
            allocate_amount, revoke_amount, request.user.email, comment
        )

        if not self._can_edit(request.user):
            logger.error(
                'User %s does not have the right to edit the budget for campaign %s',
                request.user.email,
                self.campaign.name
            )

        cbs_latest = self.campaign.get_current_budget_settings()

        with transaction.atomic():
            total = allocate_amount - revoke_amount
            if cbs_latest is not None:
                total += float(cbs_latest.total)
            cbs_new = dash.models.CampaignBudgetSettings(
                campaign=self.campaign,
                allocate=allocate_amount,
                revoke=revoke_amount,
                total=total,
                comment=comment,
                created_by=request.user
            )
            cbs_new.save(request)

    def get_history(self):
        return dash.models.CampaignBudgetSettings.objects.filter(campaign=self.campaign)

    def _can_edit(self, user):
        return self.campaign in dash.models.Campaign.objects.all().filter_by_user(user)
