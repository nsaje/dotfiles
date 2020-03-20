import json
from decimal import Decimal

import core.features.bcm
import core.features.multicurrency
from core.features.bcm import exceptions
from dash import constants
from dash import forms
from dash import models
from dash.views import helpers
from utils import api_common
from utils import exc
from utils import zlogging

logger = zlogging.getLogger(__name__)

EXCLUDE_ACCOUNTS_LOW_AMOUNT_CHECK = (431, 305)


def _can_manage_agency_margin(user, campaign):
    return user.has_perm("zemauth.can_manage_agency_margin")


def _should_add_platform_costs(user, campaign):
    return not campaign.account.uses_bcm_v2 or user.has_perm("zemauth.can_view_platform_cost_breakdown")


def _should_add_agency_costs(user, campaign):
    return (campaign.account.uses_bcm_v2 and user.has_perm("zemauth.can_view_agency_cost_breakdown")) or (
        not campaign.account.uses_bcm_v2 and user.has_perm("zemauth.can_view_agency_margin")
    )


class AccountCreditView(api_common.BaseApiView):
    def get(self, request, account_id):
        if not self.rest_proxy and not request.user.has_perm("zemauth.account_credit_view"):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)
        return self._get_response(account)

    def post(self, request, account_id):
        if not request.user.has_perm("zemauth.account_credit_view"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        request_data = json.loads(request.body)
        response_data = {"canceled": []}
        account_credits_to_cancel = models.CreditLineItem.objects.filter_by_account(account).filter(
            pk__in=request_data["cancel"]
        )

        for credit in account_credits_to_cancel:
            credit.cancel()
            response_data["canceled"].append(credit.pk)
        return self.create_api_response(response_data)

    def put(self, request, account_id):
        if not request.user.has_perm("zemauth.account_credit_view"):
            raise exc.AuthorizationError()
        account = helpers.get_account(request.user, account_id)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)

        data["status"] = constants.CreditLineItemStatus.PENDING
        if "is_agency" in data and data["is_agency"] and account.is_agency():
            data["agency"] = account.agency_id
        else:
            data["account"] = account.id

        if "is_signed" in data:
            if data["is_signed"]:
                data["status"] = constants.CreditLineItemStatus.SIGNED
            del data["is_signed"]
        if "license_fee" in data:
            data["license_fee"] = helpers.format_percent_to_decimal(data["license_fee"])

        data["currency"] = account.currency

        item = forms.CreditLineItemForm(data)

        if item.errors:
            raise exc.ValidationError(errors=item.errors)

        cli = core.features.bcm.CreditLineItem.objects.create(request, **item.cleaned_data)

        return self.create_api_response(cli.pk)

    def _prepare_credit(self, credit):
        flat_fee = credit.get_flat_fee_on_date_range(credit.start_date, credit.end_date)
        allocated = credit.get_allocated_amount()
        return {
            "id": credit.pk,
            "created_by": str(credit.created_by or "Zemanta One"),
            "created_on": credit.created_dt.date(),
            "start_date": credit.start_date,
            "end_date": credit.end_date,
            "currency": credit.currency,
            "is_signed": credit.status == constants.CreditLineItemStatus.SIGNED,
            "is_canceled": credit.status == constants.CreditLineItemStatus.CANCELED,
            "license_fee": helpers.format_decimal_to_percent(credit.license_fee) + "%",
            "flat_fee": flat_fee,
            "total": credit.effective_amount() - credit.get_refunds_amount(),
            "allocated": allocated,
            "comment": credit.comment,
            "salesforce_url": credit.get_salesforce_url(),
            "is_agency": credit.is_agency(),
            "budgets": [{"id": b.pk, "amount": b.amount} for b in credit.budgets.all()],
            "available": credit.effective_amount() - allocated,
        }

    def _get_response(self, account):
        credit_items = models.CreditLineItem.objects.filter_by_account(account)
        credit_items = credit_items.prefetch_related("budgets").order_by("-start_date", "-end_date", "-created_dt")

        return self.create_api_response(
            {
                "active": self._get_active_credit(credit_items),
                "past": self._get_past_credit(credit_items),
                "totals": self._get_credit_totals(credit_items, account),
            }
        )

    def _get_active_credit(self, credit_items):
        return [self._prepare_credit(item) for item in credit_items if not item.is_past()]

    def _get_past_credit(self, credit_items):
        return [self._prepare_credit(item) for item in credit_items if item.is_past()]

    def _get_credit_totals(self, credit_items, account):
        valid_credit_items = [
            credit for credit in credit_items if credit.status != constants.CreditLineItemStatus.PENDING
        ]
        total = sum(credit.effective_amount() for credit in valid_credit_items)
        allocated = sum(credit.get_allocated_amount() for credit in valid_credit_items if not credit.is_past())
        past = sum(credit.effective_amount() for credit in valid_credit_items if credit.is_past())
        return {
            "total": str(total),
            "allocated": str(allocated),
            "past": str(past),
            "available": str(total - allocated - past),
            "currency": account.currency,
        }


class AccountCreditItemView(api_common.BaseApiView):
    def get(self, request, account_id, credit_id):
        if not request.user.has_perm("zemauth.account_credit_view"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        item = models.CreditLineItem.objects.filter_by_account(account).get(pk=credit_id)
        return self._get_response(account, item)

    def delete(self, request, account_id, credit_id):
        if not request.user.has_perm("zemauth.account_credit_view"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)

        item = models.CreditLineItem.objects.filter_by_account(account).get(pk=credit_id)
        item.delete()

        return self.create_api_response()

    def post(self, request, account_id, credit_id):
        if not request.user.has_perm("zemauth.account_credit_view"):
            raise exc.AuthorizationError()

        account = helpers.get_account(request.user, account_id)
        item = models.CreditLineItem.objects.filter_by_account(account).get(pk=credit_id)
        request_data = json.loads(request.body)

        data = {}
        data.update(request_data)
        data["status"] = item.status

        if "is_agency" in data and data["is_agency"] and account.is_agency():
            data["account"] = None
            data["agency"] = account.agency_id
        else:
            data["account"] = account.id
            data["agency"] = None
        if "is_signed" in data:
            if data["is_signed"]:
                data["status"] = constants.CreditLineItemStatus.SIGNED
            del data["is_signed"]
        if "license_fee" in data:
            data["license_fee"] = helpers.format_percent_to_decimal(data["license_fee"])
        item_form = forms.CreditLineItemForm(data, instance=item)

        if item_form.errors:
            raise exc.ValidationError(errors=item_form.errors)

        item_form.save(request=request, action_type=constants.HistoryActionType.CREDIT_CHANGE)
        return self.create_api_response(credit_id)

    def _get_response(self, account, item):
        return self.create_api_response(
            {
                "id": item.pk,
                "created_by": str(item.created_by or "Zemanta One"),
                "created_on": item.created_dt.date(),
                "start_date": item.start_date,
                "end_date": item.end_date,
                "currency": item.currency,
                "is_signed": item.status == constants.CreditLineItemStatus.SIGNED,
                "is_canceled": item.status == constants.CreditLineItemStatus.CANCELED,
                "license_fee": helpers.format_decimal_to_percent(item.license_fee) + "%",
                "amount": item.amount,
                "account_id": account.id,
                "comment": item.comment,
                "is_agency": item.is_agency(),
                "salesforce_url": item.get_salesforce_url(),
                "contract_id": item.contract_id,
                "contract_number": item.contract_number,
                "budgets": [
                    {
                        "campaign": str(b.campaign),
                        "id": b.pk,
                        "total": b.allocated_amount(),
                        "spend": (
                            b.get_local_spend_data()["etfm_total"]
                            if account.uses_bcm_v2
                            else b.get_local_spend_data()["etf_total"]
                        ),
                        "start_date": b.start_date,
                        "end_date": b.end_date,
                        "currency": item.currency,
                        "comment": b.comment,
                    }
                    for b in item.budgets.all().order_by("-created_dt")[:100]
                ],
            }
        )


class CampaignBudgetView(api_common.BaseApiView):
    def get(self, request, campaign_id):
        campaign = helpers.get_campaign(request.user, campaign_id, select_related=True)
        return self._get_response(request.user, campaign)

    def put(self, request, campaign_id):
        if request.user.has_perm("zemauth.disable_budget_management"):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id, select_related=True)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)

        data["campaign"] = campaign.id
        if "margin" in data:
            if not _can_manage_agency_margin(request.user, campaign):
                del data["margin"]
            else:
                data["margin"] = helpers.format_percent_to_decimal(data["margin"] or "0")

        form = forms.BudgetLineItemForm(data)

        try:
            form.is_valid()

        except exc.ValidationError:
            if form.errors:
                raise exc.ValidationError(errors=form.errors)

        try:
            item = core.features.bcm.BudgetLineItem.objects.create(
                request=request,
                campaign=campaign,
                credit=form.cleaned_data["credit"],
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data["end_date"],
                amount=form.cleaned_data["amount"],
                margin=form.cleaned_data["margin"],
                comment=form.cleaned_data["comment"],
            )

        except exc.MultipleValidationError as err:
            _handle_multiple_errors(err)

        except exceptions.CanNotSetMargin as err:
            raise exc.ValidationError(errors={"margin": [str(err)]})

        except exceptions.CanNotChangeStartDate as err:
            raise exc.ValidationError(errors={"start_date": [str(err)]})

        except exceptions.CanNotChangeBudget as err:
            raise exc.ValidationError(str(err))

        except exceptions.CreditCanceled as err:
            raise exc.ValidationError(errors={"credit": [str(err)]})

        except exceptions.StartDateInThePast as err:
            raise exc.ValidationError(errors={"start_date": [str(err)]})

        except exceptions.EndDateInThePast as err:
            raise exc.ValidationError(errors={"end_date": [str(err)]})

        return self.create_api_response(item.pk)

    def _prepare_item(self, user, campaign, item):
        spend_data = item.get_local_spend_data()

        if campaign.account.uses_bcm_v2:
            spend = spend_data["etfm_total"]
        else:
            spend = spend_data["etf_total"]

        allocated = item.allocated_amount()
        result = {
            "id": item.pk,
            "start_date": item.start_date,
            "credit": item.credit.id,  # FIXME(nsaje) hack to return credit id in REST API
            "end_date": item.end_date,
            "state": item.state(),
            "currency": item.credit.currency,
            "total": allocated,
            "spend": spend,
            "available": allocated - spend,
            "is_editable": item.is_editable(),
            "is_updatable": item.is_updatable(),
            "comment": item.comment,
        }

        if _should_add_platform_costs(user, campaign):
            result["license_fee"] = helpers.format_decimal_to_percent(item.credit.license_fee) + "%"

        if _should_add_agency_costs(user, campaign):
            result["margin"] = helpers.format_decimal_to_percent(item.margin) + "%"

        return result

    def _get_response(self, user, campaign):
        budget_items = (
            models.BudgetLineItem.objects.filter(campaign_id=campaign.id)
            .select_related("credit")
            .order_by("-created_dt")
            .annotate_spend_data()
        )
        credit_items = (
            models.CreditLineItem.objects.filter_by_account(campaign.account)
            .filter(currency=campaign.account.currency)
            .prefetch_related("budgets")
        )

        active_budget = self._get_active_budget(user, campaign, budget_items)
        return self.create_api_response(
            {
                "active": active_budget,
                "past": self._get_past_budget(user, campaign, budget_items),
                "totals": self._get_budget_totals(user, campaign, active_budget, budget_items, credit_items),
                "credits": self._get_available_credit_items(user, campaign, credit_items),
            }
        )

    def _get_available_credit_items(self, user, campaign, available_credits):
        credits = []
        for credit in available_credits:
            credit_dict = {
                "id": credit.pk,
                "total": credit.effective_amount(),
                "available": credit.effective_amount() - credit.get_allocated_amount(),
                "start_date": credit.start_date,
                "end_date": credit.end_date,
                "currency": credit.currency,
                "comment": credit.comment,
                "is_available": credit.is_available(),
                "is_agency": credit.is_agency(),
            }

            if _should_add_platform_costs(user, campaign):
                credit_dict["license_fee"] = helpers.format_decimal_to_percent(credit.license_fee)
            credits.append(credit_dict)

        return credits

    def _get_active_budget(self, user, campaign, items):
        return [
            self._prepare_item(user, campaign, b)
            for b in items
            if b.state() in (constants.BudgetLineItemState.ACTIVE, constants.BudgetLineItemState.PENDING)
        ]

    def _get_past_budget(self, user, campaign, items):
        return [
            self._prepare_item(user, campaign, b)
            for b in items
            if b.state() in (constants.BudgetLineItemState.DEPLETED, constants.BudgetLineItemState.INACTIVE)
        ]

    def _get_budget_totals(self, user, campaign, active_budget, budget_items, credits):
        data = {
            "current": {
                "available": sum([x["available"] for x in active_budget]),
                "unallocated": Decimal("0.0000"),
                "past": Decimal("0.0000"),
            },
            "lifetime": {"campaign_spend": Decimal("0.0000")},
            "currency": campaign.account.currency,
        }

        if _should_add_platform_costs(user, campaign):
            data["lifetime"]["media_spend"] = Decimal("0.0000")
            data["lifetime"]["data_spend"] = Decimal("0.0000")
            data["lifetime"]["license_fee"] = Decimal("0.0000")

        if _should_add_agency_costs(user, campaign):
            data["lifetime"]["margin"] = Decimal("0.0000")

        for item in credits:
            if item.status != constants.CreditLineItemStatus.SIGNED or item.is_past():
                continue
            data["current"]["unallocated"] += Decimal(item.amount - item.flat_fee() - item.get_allocated_amount())

        for item in budget_items:
            if item.state() == constants.BudgetLineItemState.PENDING:
                continue

            spend_data = item.get_local_spend_data()

            if campaign.account.uses_bcm_v2:
                data["lifetime"]["campaign_spend"] += spend_data["etfm_total"]
            else:
                data["lifetime"]["campaign_spend"] += spend_data["etf_total"]

            if _should_add_platform_costs(user, campaign):
                data["lifetime"]["media_spend"] += spend_data["media"]
                data["lifetime"]["data_spend"] += spend_data["data"]
                data["lifetime"]["license_fee"] += spend_data["license_fee"]

            if _should_add_agency_costs(user, campaign):
                data["lifetime"]["margin"] += spend_data["margin"]

        return data


class CampaignBudgetItemView(api_common.BaseApiView):
    def get(self, request, campaign_id, budget_id):
        helpers.get_campaign(request.user, campaign_id, select_related=True)
        try:
            item = models.BudgetLineItem.objects.get(campaign_id=campaign_id, pk=budget_id)
        except models.BudgetLineItem.DoesNotExist:
            raise exc.MissingDataError("Budget does not exist!")
        return self._get_response(request.user, item)

    def post(self, request, campaign_id, budget_id):
        if request.user.has_perm("zemauth.disable_budget_management"):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id, select_related=True)

        request_data = json.loads(request.body)
        data = {}
        data.update(request_data)
        if "margin" in data:
            if not _can_manage_agency_margin(request.user, campaign):
                del data["margin"]
            else:
                data["margin"] = helpers.format_percent_to_decimal(data["margin"] or "0")

        data["campaign"] = campaign.id

        instance = models.BudgetLineItem.objects.get(campaign_id=campaign_id, pk=budget_id)
        item = forms.BudgetLineItemForm(data, instance=instance)
        try:
            if item.errors:
                raise exc.ValidationError(errors=item.errors)
            # TODO: call update instead of explicitly save
            item.save(request=request, action_type=constants.HistoryActionType.BUDGET_CHANGE)

        except exc.MultipleValidationError as err:
            _handle_multiple_errors(err)

        except exceptions.CanNotSetMargin as err:
            raise exc.ValidationError(errors={"margin": [str(err)]})

        except exceptions.CanNotChangeStartDate as err:
            raise exc.ValidationError(errors={"start_date": [str(err)]})

        except exceptions.CanNotChangeBudget as err:
            raise exc.ValidationError(str(err))

        except exceptions.CreditCanceled as err:
            raise exc.ValidationError(errors={"credit": [str(err)]})

        except exceptions.StartDateInThePast as err:
            raise exc.ValidationError(errors={"start_date": [str(err)]})

        except exceptions.EndDateInThePast as err:
            raise exc.ValidationError(errors={"end_date": [str(err)]})

        return self.create_api_response({"id": item.instance.pk})

    def delete(self, request, campaign_id, budget_id):
        if request.user.has_perm("zemauth.disable_budget_management"):
            raise exc.AuthorizationError()

        campaign = helpers.get_campaign(request.user, campaign_id)
        item = models.BudgetLineItem.objects.get(campaign_id=campaign.id, pk=budget_id)
        try:
            item.delete()
        except AssertionError:
            raise exc.ValidationError("Budget item is not pending")
        campaign.write_history(
            "Deleted budget", action_type=constants.HistoryActionType.BUDGET_CHANGE, user=request.user
        )
        return self.create_api_response(True)

    def _get_response(self, user, item):
        if user.has_perm("zemauth.can_manage_budgets_in_local_currency"):
            spend_data = item.get_local_spend_data()
        else:
            spend_data = item.get_spend_data()

        if item.campaign.account.uses_bcm_v2:
            spend = spend_data["etfm_total"]
        else:
            spend = spend_data["etf_total"]
        allocated = item.allocated_amount()
        response = {
            "id": item.id,
            "amount": item.amount,
            "spend": spend,
            "available": allocated - spend,
            "created_by": str(item.created_by or "Zemanta One"),
            "created_at": item.created_dt,
            "start_date": item.start_date,
            "end_date": item.end_date,
            "comment": item.comment,
            "is_editable": item.is_editable(),
            "is_updatable": item.is_updatable(),
            "state": item.state(),
            "currency": item.credit.currency,
            "credit": {"id": item.credit.pk, "name": str(item.credit), "license_fee": item.credit.license_fee},
        }
        if user.has_perm("zemauth.can_view_agency_margin"):
            response["margin"] = helpers.format_decimal_to_percent(item.margin) + "%"
        return self.create_api_response(response)


def _handle_multiple_errors(err):
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
            errors.setdefault("credit", []).append(str(e))

        elif isinstance(e, exceptions.CreditPending):
            errors.setdefault("credit", []).append(str(e))

        elif isinstance(e, exceptions.CurrencyInconsistent):
            errors.setdefault("credit", []).append(str(e))

        elif isinstance(e, exceptions.OverlappingBudgets):
            errors.setdefault("credit", []).append(str(e))

        elif isinstance(e, exceptions.CampaignHasNoCredit):
            errors.setdefault("credit", []).append(str(e))

        elif isinstance(e, exceptions.MarginRangeInvalid):
            errors.setdefault("margin", []).append(str(e))

        elif isinstance(e, exceptions.OverlappingBudgetMarginInvalid):
            errors.setdefault("margin", []).append(str(e))

    raise exc.ValidationError(errors=errors)
