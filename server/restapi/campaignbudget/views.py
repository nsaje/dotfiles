from django.db import transaction

import core.models
import restapi.access
import utils.exc
from core.features.bcm import exceptions
from dash import constants
from restapi.common.pagination import StandardPagination
from restapi.common.views_base import RESTAPIBaseViewSet

from . import serializers


class CampaignBudgetViewSet(RESTAPIBaseViewSet):
    def get(self, request, campaign_id, budget_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id, select_related=True)
        budget = self._get_budget(campaign, budget_id)
        return self.response_ok(serializers.CampaignBudgetSerializer(budget).data)

    def put(self, request, campaign_id, budget_id):
        if request.user.has_perm("zemauth.disable_budget_management"):
            raise utils.exc.AuthorizationError()

        campaign = restapi.access.get_campaign(request.user, campaign_id, select_related=True)
        serializer = serializers.CampaignBudgetSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        budget = self._get_budget(campaign, budget_id)
        self._update_budget(budget.update, request=request, **serializer.validated_data)
        return self.response_ok(serializers.CampaignBudgetSerializer(budget).data)

    def list(self, request, campaign_id):
        campaign = restapi.access.get_campaign(request.user, campaign_id, select_related=True)
        budgets = (
            core.features.bcm.BudgetLineItem.objects.filter(campaign=campaign)
            .select_related("credit", "campaign__account")
            .order_by("-created_dt")
        )
        active_budgets = [
            b
            for b in budgets
            if b.state() in (constants.BudgetLineItemState.ACTIVE, constants.BudgetLineItemState.PENDING)
        ]
        paginator = StandardPagination()
        budgets_paginated = paginator.paginate_queryset(active_budgets, request)
        return paginator.get_paginated_response(serializers.CampaignBudgetSerializer(budgets_paginated, many=True).data)

    def create(self, request, campaign_id):
        if request.user.has_perm("zemauth.disable_budget_management"):
            raise utils.exc.AuthorizationError()

        campaign = restapi.access.get_campaign(request.user, campaign_id, select_related=True)
        serializer = serializers.CampaignBudgetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_budget_data = serializer.validated_data
        credit = self._get_credit(campaign, new_budget_data.get("credit", {}).get("id"))
        new_budget = self._update_budget(
            core.features.bcm.BudgetLineItem.objects.create,
            request=request,
            campaign=campaign,
            credit=credit,
            start_date=new_budget_data.get("start_date"),
            end_date=new_budget_data.get("end_date"),
            amount=new_budget_data.get("amount"),
        )
        return self.response_ok(serializers.CampaignBudgetSerializer(new_budget).data, status=201)

    @staticmethod
    def _get_budget(campaign, budget_id):
        try:
            budget = core.features.bcm.BudgetLineItem.objects.get(campaign=campaign, pk=budget_id)
        except core.features.bcm.BudgetLineItem.DoesNotExist:
            raise utils.exc.MissingDataError("Budget does not exist!")
        return budget

    @staticmethod
    def _get_credit(campaign, credit_id):
        try:
            credit = core.features.bcm.CreditLineItem.objects.filter_by_account(account=campaign.account).get(
                id=credit_id
            )
        except core.features.bcm.CreditLineItem.DoesNotExist:
            raise utils.exc.MissingDataError("Credit does not exist!")
        return credit

    @staticmethod
    @transaction.atomic
    def _update_budget(budget_update, **kwargs):
        try:
            new_budget = budget_update(**kwargs)

        except utils.exc.MultipleValidationError as err:
            errors = {}
            for e in err.errors:
                if isinstance(e, exceptions.StartDateInvalid):
                    errors.setdefault("start_date", []).append(str(e))

                elif isinstance(e, exceptions.EndDateInvalid):
                    errors.setdefault("end_date", []).append(str(e))

                elif isinstance(e, exceptions.StartDateBiggerThanEndDate):
                    errors.setdefault("end_date", []).append(str(e))

                elif isinstance(e, exceptions.BudgetAmountCannotChange):
                    errors.setdefault("amount", []).append(str(e))

                elif isinstance(e, exceptions.BudgetAmountNegative):
                    errors.setdefault("amount", []).append(str(e))

                elif isinstance(e, exceptions.BudgetAmountExceededCreditAmount):
                    errors.setdefault("amount", []).append(str(e))

                elif isinstance(e, exceptions.BudgetAmountTooLow):
                    errors.setdefault("amount", []).append(str(e))

                elif isinstance(e, exceptions.CampaignStopDisabled):
                    errors.setdefault("amount", []).append(str(e))

                elif isinstance(e, exceptions.CanNotChangeCredit):
                    errors.setdefault("credit_id", []).append(str(e))

                elif isinstance(e, exceptions.CreditPending):
                    errors.setdefault("credit_id", []).append(str(e))

                elif isinstance(e, exceptions.CurrencyInconsistent):
                    errors.setdefault("credit_id", []).append(str(e))

                elif isinstance(e, exceptions.OverlappingBudgets):
                    errors.setdefault("credit_id", []).append(str(e))

                elif isinstance(e, exceptions.CampaignHasNoCredit):
                    errors.setdefault("credit_id", []).append(str(e))

                elif isinstance(e, exceptions.MarginRangeInvalid):
                    errors.setdefault("margin", []).append(str(e))

                elif isinstance(e, exceptions.OverlappingBudgetMarginInvalid):
                    errors.setdefault("margin", []).append(str(e))

            raise utils.exc.ValidationError(errors=errors)

        except exceptions.CanNotChangeStartDate as err:
            raise utils.exc.ValidationError(errors={"start_date": [str(err)]})

        except exceptions.CanNotChangeBudget as err:
            raise utils.exc.ValidationError(str(err))

        except exceptions.CreditCanceled as err:
            raise utils.exc.ValidationError(errors={"credit_id": [str(err)]})

        except exceptions.StartDateInThePast as err:
            raise utils.exc.ValidationError(errors={"start_date": [str(err)]})

        except exceptions.EndDateInThePast as err:
            raise utils.exc.ValidationError(errors={"end_date": [str(err)]})

        return new_budget
