# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import F
from django.db.models import Q
from django.db.models import Sum
from django.forms.models import model_to_dict

import core.common
import core.features.bcm
import core.features.bcm.helpers
import core.features.history
import core.features.multicurrency
import utils.dates_helper
import utils.demo_anonymizer
import utils.string_helper
from dash import constants
from utils import converters
from utils import dates_helper
from utils import lc_helper
from utils import validation_helper

from . import credit_line_item
from . import dailystatement
from . import exceptions
from . import helpers

EXCLUDE_ACCOUNTS_LOW_AMOUNT_CHECK = (431, settings.HARDCODED_ACCOUNT_ID_OEN, settings.HARDCODED_ACCOUNT_ID_INPOWERED_1)
SKIP_AMOUNT_VALIDATION_CREDIT_IDS = [1251]
UPDATABLE_FIELDS = ("start_date", "end_date", "amount", "comment")


class BudgetLineItemManager(core.common.QuerySetManager):
    @transaction.atomic
    def create(self, request, campaign, credit, start_date, end_date, amount, margin=None, comment=None):
        core.common.entity_limits.enforce(
            BudgetLineItem.objects.filter(campaign=campaign).filter_present_and_future(), campaign.account_id
        )
        item = BudgetLineItem(campaign=campaign, credit=credit, start_date=start_date, end_date=end_date, amount=amount)
        if margin is not None:
            item.margin = margin
        if comment is not None:
            item.comment = comment

        item.clean_start_date()
        item.clean_end_date()
        item.save(request=request, action_type=constants.HistoryActionType.CREATE)

        return item

    def clone(self, request, source_budget, campaign):
        core.common.entity_limits.enforce(
            BudgetLineItem.objects.filter(campaign=campaign).filter_present_and_future(), campaign.account_id
        )

        today = dates_helper.local_today()
        start_date = today if source_budget.start_date < today else source_budget.start_date

        with transaction.atomic():
            item = BudgetLineItem(campaign=campaign, credit=source_budget.credit, start_date=start_date)
            for field in set(BudgetLineItem._clone_fields):
                setattr(item, field, getattr(source_budget, field))
            item.save(request)

        return item


class BudgetLineItem(core.common.FootprintModel, core.features.history.HistoryMixinOld):
    class Meta:
        app_label = "dash"

    _clone_fields = ["end_date", "margin", "amount", "comment"]

    history_fields = ["start_date", "end_date", "amount", "freed_cc", "comment"]

    _demo_fields = {"comment": lambda: "Monthly budget"}
    campaign = models.ForeignKey("Campaign", related_name="budgets", on_delete=models.PROTECT)
    credit = models.ForeignKey("CreditLineItem", related_name="budgets", on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    margin = models.DecimalField(decimal_places=4, max_digits=5, default=Decimal("0"))

    amount = models.IntegerField()
    freed_cc = models.BigIntegerField(default=0)

    comment = models.CharField(max_length=256, blank=True, null=True)

    created_dt = models.DateTimeField(auto_now_add=True, verbose_name="Created at")
    modified_dt = models.DateTimeField(auto_now=True, verbose_name="Modified at")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="+",
        verbose_name="Created by",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    objects = BudgetLineItemManager()

    def __str__(self):
        return "{currency_symbol}{amount} - from {start_date} to {end_date} (id: {id}, campaign: {campaign})".format(
            currency_symbol=core.features.multicurrency.get_currency_symbol(self.credit.currency),
            amount=self.amount,
            start_date=self.start_date,
            end_date=self.end_date,
            id=self.id,
            campaign=str(self.campaign),
        )

    @classmethod
    def get_human_prop_name(cls, prop_name):
        NAMES = {
            "start_date": "Start Date",
            "end_date": "End Date",
            "amount": "Amount",
            "freed_cc": "Released amount",
            "margin": "Margin",
            "comment": "Comment",
        }
        return NAMES.get(prop_name)

    def get_human_value(self, prop_name, value):
        currency_symbol = core.features.multicurrency.get_currency_symbol(self.credit.currency)
        if prop_name == "amount" and value is not None:
            value = lc_helper.format_currency(value, places=2, curr=currency_symbol)
        elif prop_name == "freed_cc" and value is not None:
            value = lc_helper.format_currency(
                Decimal(value) * converters.CC_TO_DECIMAL_CURRENCY, places=2, curr=currency_symbol
            )
        elif prop_name == "margin" and value is not None:
            value = "{}%".format(utils.string_helper.format_decimal(Decimal(value) * 100, 2, 3))
        elif prop_name == "comment":
            value = value or ""
        return value

    def get_settings_dict(self):
        return {history_key: getattr(self, history_key) for history_key in self.history_fields}

    @transaction.atomic
    def update(self, request, **updates) -> bool:
        has_changes = False
        for field, new_value in updates.items():
            if field not in UPDATABLE_FIELDS:
                continue
            if new_value != getattr(self, field):
                has_changes = True
                setattr(self, field, new_value)
                if field == "start_date":
                    self.clean_start_date()
                elif field == "end_date":
                    self.clean_end_date()
        if has_changes:
            self.save(request=request, action_type=constants.HistoryActionType.BUDGET_CHANGE)
        return has_changes

    @transaction.atomic
    def save(self, request=None, user=None, action_type=None, *args, **kwargs):
        import core.features.bcm

        # lock credit for the duration of the save
        credit_line_item.CreditLineItem.objects.select_for_update().get(pk=self.credit.id)
        self.credit.refresh_from_db()

        self.full_clean()
        if user and not self.pk:
            self.created_by = user
        elif request and not self.pk:
            self.created_by = request.user
        super(BudgetLineItem, self).save(*args, **kwargs)
        core.features.bcm.BudgetHistory.objects.create(
            created_by=request.user if request else user or None, snapshot=model_to_dict(self), budget=self
        )
        self.add_to_history(request and request.user or user or None, action_type)
        helpers.notify_budget_to_slack(self, action_type=action_type)

    def add_to_history(self, user, action_type):
        changes = self.get_model_state_changes(model_to_dict(self))
        # this is a temporary state until cleaning up of settings changes text
        if not changes and not self.post_init_newly_created:
            return None, ""

        if self.post_init_newly_created:
            changes = self.get_history_dict()

        changes, changes_text = self.construct_changes(
            "Created budget.", "Budget: #{}.".format(self.id) if self.id else None, changes
        )
        self.campaign.write_history(changes_text, changes=changes, action_type=action_type, user=user)

    def db_state(self, date=None):
        return BudgetLineItem.objects.get(pk=self.pk).state(date=date)

    def delete(self):
        if self.db_state() != constants.BudgetLineItemState.PENDING:
            raise AssertionError("Cannot delete nonpending budgets")
        super(BudgetLineItem, self).delete()

    def get_overlap(self, start_date, end_date):
        return utils.dates_helper.get_overlap(self.start_date, self.end_date, start_date, end_date)

    def get_available_etfm_amount(self, date=None):
        if date is None:
            date = utils.dates_helper.local_today()
        local_available_etfm = self.get_local_available_etfm_amount(date)
        exchange_rate = core.features.multicurrency.get_exchange_rate(date, self.credit.currency)
        return local_available_etfm / exchange_rate

    def get_local_available_etfm_amount(self, date=None):
        if date is None:
            date = utils.dates_helper.local_today()
        total_spend = self.get_local_spend_data(to_date=date)["etfm_total"]
        return self.allocated_amount() - total_spend

    def get_local_etfm_spend_data(self):
        return self.get_local_spend_data()["etfm_total"]

    def get_local_etfm_available_data(self):
        return self.get_local_available_etfm_amount()

    def state(self, date=None):
        if date is None:
            date = utils.dates_helper.local_today()
        if self.get_available_etfm_amount(date) <= 0:
            return constants.BudgetLineItemState.DEPLETED
        if self.end_date and self.end_date < date:
            return constants.BudgetLineItemState.INACTIVE
        if self.start_date and self.start_date <= date:
            return constants.BudgetLineItemState.ACTIVE
        return constants.BudgetLineItemState.PENDING

    def state_text(self, date=None):
        return constants.BudgetLineItemState.get_text(self.state(date=date))

    def allocated_amount_cc(self):
        return self.amount * converters.CURRENCY_TO_CC - self.freed_cc

    def allocated_amount(self):
        return Decimal(self.allocated_amount_cc()) * converters.CC_TO_DECIMAL_CURRENCY

    def is_editable(self):
        return self.state() == constants.BudgetLineItemState.PENDING

    def is_updatable(self):
        return self.state() == constants.BudgetLineItemState.ACTIVE

    def can_edit_start_date(self):
        return self.state() == constants.BudgetLineItemState.PENDING

    def can_edit_end_date(self):
        return (
            self.state() == constants.BudgetLineItemState.PENDING
            or self.state() == constants.BudgetLineItemState.ACTIVE
        )

    def can_edit_amount(self):
        return (
            self.state() == constants.BudgetLineItemState.PENDING
            or self.state() == constants.BudgetLineItemState.ACTIVE
        )

    def minimize_amount_and_end_today(self):
        import automation.campaignstop

        local_today = utils.dates_helper.local_today()
        if self.end_date < local_today:
            return

        if self.state() not in (constants.BudgetLineItemState.ACTIVE, constants.BudgetLineItemState.PENDING):
            return

        if self.campaign.real_time_campaign_stop:
            min_amount = automation.campaignstop.calculate_minimum_budget_amount(self)
            if min_amount < self.amount:
                self.amount = min_amount
        self.end_date = max(local_today, self.start_date)
        self.save()

    def free_inactive_allocated_assets(self):
        if self.state() != constants.BudgetLineItemState.INACTIVE:
            raise AssertionError("Budget has to be inactive to be freed.")
        amount_cc = self.amount * converters.CURRENCY_TO_CC
        spend_data = self.get_local_spend_data()
        total_spend = int(spend_data["etfm_total"] * converters.CURRENCY_TO_CC)

        reserve = self.get_reserve_amount_cc()
        free_date = self.end_date + datetime.timedelta(days=settings.LAST_N_DAY_REPORTS)
        is_over_sync_time = utils.dates_helper.local_today() > free_date

        if is_over_sync_time:
            # After we completed all syncs, free all the assets including
            # reserve
            self.freed_cc = max(0, amount_cc - total_spend)
        elif self.freed_cc == 0 and reserve is not None:
            self.freed_cc = max(0, amount_cc - total_spend - reserve)

        self.save()

    def get_reserve_amount_cc(self, factor_offset=0):
        try:
            # try to get previous statement that has more solid data
            statement = list(self.statements.all().order_by("-date")[:2])[-1]
        except IndexError:
            return None
        total_cc = converters.nano_to_cc(
            statement.local_base_media_spend_nano
            + statement.local_base_data_spend_nano
            + statement.local_service_fee_nano
            + statement.local_license_fee_nano
            + statement.local_margin_nano
        )
        return total_cc * (factor_offset + settings.BUDGET_RESERVE_FACTOR)

    def get_latest_statement(self):
        return self.statements.all().order_by("-date").first()

    def get_latest_statement_qs(self):
        latest_statement = self.get_latest_statement()
        if not latest_statement:
            return core.features.bcm.BudgetDailyStatement.objects.none()
        return self.statements.filter(id=latest_statement.id)

    def get_spend_data(self, date=None):
        if (date is None or date == utils.dates_helper.local_today()) and hasattr(self, "spend_data_b_media"):
            return {
                "base_media": utils.converters.nano_to_decimal(self.spend_data_b_media or 0),
                "base_data": utils.converters.nano_to_decimal(self.spend_data_b_data or 0),
                "media": utils.converters.nano_to_decimal(self.spend_data_e_media or 0),
                "data": utils.converters.nano_to_decimal(self.spend_data_e_data or 0),
                "service_fee": utils.converters.nano_to_decimal(self.spend_data_service_fee or 0),
                "license_fee": utils.converters.nano_to_decimal(self.spend_data_license_fee or 0),
                "margin": utils.converters.nano_to_decimal(self.spend_data_margin or 0),
                "et_total": utils.converters.nano_to_decimal(self.spend_data_et_total or 0),
                "etf_total": utils.converters.nano_to_decimal(self.spend_data_etf_total or 0),
                "etfm_total": utils.converters.nano_to_decimal(self.spend_data_etfm_total or 0),
            }
        statements = self.statements
        if date:
            statements = statements.filter(date__lte=date)
        return statements.calculate_spend_data()

    def get_local_spend_data(self, from_date=None, to_date=None):
        if (
            from_date is None
            and (to_date is None or to_date == utils.dates_helper.local_today())
            and hasattr(self, "spend_data_b_media")
        ):
            return {
                "base_media": utils.converters.nano_to_decimal(self.spend_data_local_b_media or 0),
                "base_data": utils.converters.nano_to_decimal(self.spend_data_local_b_data or 0),
                "media": utils.converters.nano_to_decimal(self.spend_data_local_e_media or 0),
                "data": utils.converters.nano_to_decimal(self.spend_data_local_e_data or 0),
                "service_fee": utils.converters.nano_to_decimal(self.spend_data_local_service_fee or 0),
                "license_fee": utils.converters.nano_to_decimal(self.spend_data_local_license_fee or 0),
                "margin": utils.converters.nano_to_decimal(self.spend_data_local_margin or 0),
                "etfm_total": utils.converters.nano_to_decimal(self.spend_data_local_etfm_total or 0),
            }
        statements = self.statements
        if from_date:
            statements = statements.filter(date__gte=from_date)
        if to_date:
            statements = statements.filter(date__lte=to_date)
        return statements.calculate_local_spend_data()

    def get_daily_spend(self, date):
        if not date:
            date = utils.dates_helper.local_today()
        statement = self.statements.filter(date=date)
        return statement.calculate_spend_data()

    def get_ideal_budget_spend(self, date):
        """
        Ideal budget spend at END of specified date.
        """
        if date < self.start_date:
            return 0
        elif date >= self.end_date:
            return self.amount

        date_start_diff = (date - self.start_date).days + 1
        date_total_diff = (self.end_date - self.start_date).days + 1

        return self.amount * Decimal(date_start_diff) / Decimal(date_total_diff)

    def clean(self):
        if self.pk:
            db_state = self.db_state()
            if self.has_changed("margin"):
                raise exceptions.CanNotSetMargin("Margin can only be set on newly created budget items.")
            if self.has_changed("start_date") and not db_state == constants.BudgetLineItemState.PENDING:
                raise exceptions.CanNotChangeStartDate("Only pending budgets can change start date and amount.")
            is_reserve_update = all(
                [
                    not self.has_changed("start_date"),
                    not self.has_changed("end_date"),
                    not self.has_changed("amount"),
                    not self.has_changed("campaign"),
                ]
            )
            if not is_reserve_update and db_state not in (
                constants.BudgetLineItemState.PENDING,
                constants.BudgetLineItemState.ACTIVE,
            ):
                raise exceptions.CanNotChangeBudget("Only pending and active budgets can change.")
        elif self.credit.status == constants.CreditLineItemStatus.CANCELED:
            raise exceptions.CreditCanceled("Canceled credits cannot have new budget items.")

        validation_helper.validate_multiple(
            self.validate_start_date,
            self.validate_end_date,
            self.validate_amount,
            self.validate_credit,
            self.validate_campaign,
            self.validate_margin,
        )

    def service_fee(self):
        return self.credit.service_fee

    def license_fee(self):
        return self.credit.license_fee

    def validate_campaign(self):
        is_valid_account_credit = self.credit.account_id and self.campaign.account_id == self.credit.account_id
        is_valid_agency_credit = self.credit.agency_id and self.campaign.account.agency_id == self.credit.agency_id
        if not (is_valid_account_credit or is_valid_agency_credit):
            raise exceptions.CampaignHasNoCredit("Campaign has no credit.")

    def validate_credit(self):
        if self.has_changed("credit"):
            raise exceptions.CanNotChangeCredit("Credit cannot change.")
        if self.credit.status == constants.CreditLineItemStatus.PENDING:
            raise exceptions.CreditPending("Cannot allocate budget from an unsigned credit.")
        if self.credit.currency != self.campaign.account.currency:
            raise exceptions.CurrencyInconsistent(
                "Cannot allocate budget from a credit in currency different from account's currency."
            )

        self.validate_fees()

    def clean_start_date(self):
        """
        Due to testing and manual adjustments budgets sometimes need
        to be created in the past. 'Date in the past' checks therefore
        aren't called automatically like 'clean_' methods usually are.
        """
        if not self.pk or self.has_changed("start_date"):
            if self.start_date < utils.dates_helper.local_today():
                raise exceptions.StartDateInThePast("Start date has to be in the future.")

    def clean_end_date(self):
        if not self.pk or self.has_changed("end_date"):
            if self.end_date < utils.dates_helper.local_today():
                raise exceptions.EndDateInThePast("End date has to be in the future.")

    def validate_start_date(self):
        if not self.start_date:
            return
        if self.start_date < self.credit.start_date:
            raise exceptions.StartDateInvalid("Start date cannot be smaller than the credit's start date.")

    def validate_end_date(self):
        if not self.end_date:
            return
        if self.end_date > self.credit.end_date:
            raise exceptions.EndDateInvalid("End date cannot be bigger than the credit's end date.")
        if self.start_date and self.start_date > self.end_date:
            raise exceptions.StartDateBiggerThanEndDate("Start date cannot be bigger than the end date.")

    def validate_margin(self):
        if not (0 <= self.margin < 1):
            raise exceptions.MarginRangeInvalid("Margin must be between 0 and 100%.")

        if self.start_date is None or self.end_date is None:
            return

        overlapping_budget_line_items = (
            BudgetLineItem.objects.filter(campaign=self.campaign)
            .exclude(margin=self.margin)
            .filter_overlapping(self.start_date, self.end_date)
        )
        if overlapping_budget_line_items.exists():
            raise exceptions.OverlappingBudgetMarginInvalid("Margin must be the same on overlapping budget line items.")

    def validate_fees(self):
        if self.start_date is None or self.end_date is None:
            return

        overlapping_budget_line_items = (
            BudgetLineItem.objects.filter(campaign=self.campaign)
            .exclude(credit__service_fee=self.credit.service_fee, credit__license_fee=self.credit.license_fee)
            .filter_overlapping(self.start_date, self.end_date)
        )
        if overlapping_budget_line_items.exists():
            raise exceptions.OverlappingBudgets("Unable to add budget with chosen credit. Choose another credit.")

    def validate_amount(self):
        if self.has_changed("amount") and self.credit.status == constants.CreditLineItemStatus.CANCELED:
            raise exceptions.BudgetAmountCannotChange("Canceled credit's budget amounts cannot change.")
        if self.amount < 0:
            raise exceptions.BudgetAmountNegative("Amount cannot be negative.")

        if self.credit_id in SKIP_AMOUNT_VALIDATION_CREDIT_IDS:
            return

        self._validate_amount_campaign_stop()

        budgets = self.credit.budgets.exclude(pk=self.pk)
        delta = self.credit.effective_amount() - sum(b.allocated_amount() for b in budgets) - self.allocated_amount()
        if delta < 0:
            raise exceptions.BudgetAmountExceededCreditAmount(
                "Budget exceeds the total credit amount by {currency_symbol}{delta}.".format(
                    currency_symbol=core.features.multicurrency.get_currency_symbol(self.credit.currency),
                    delta=-delta.quantize(Decimal("1.00")),
                )
            )

    def _validate_amount_campaign_stop(self):
        import automation.campaignstop

        prev_amount = self.previous_value("amount")
        if prev_amount is None:
            return

        if self.amount >= prev_amount:
            return
        if self.campaign.real_time_campaign_stop:
            min_amount = automation.campaignstop.calculate_minimum_budget_amount(self)
            if self.amount < min_amount:
                raise exceptions.BudgetAmountTooLow(
                    "Budget amount has to be at least {currency_symbol}{min_amount:.2f}.".format(
                        currency_symbol=core.features.multicurrency.get_currency_symbol(self.credit.currency),
                        min_amount=min_amount,
                    )
                )
        else:
            acc_id = self.campaign.account_id
            if self.amount < prev_amount and acc_id not in EXCLUDE_ACCOUNTS_LOW_AMOUNT_CHECK:
                raise exceptions.CampaignStopDisabled("If campaign stop is disabled amount cannot be lowered.")
                return

    @classmethod
    def get_defaults_dict(cls):
        return {}

    class QuerySet(models.QuerySet):
        def delete(self):
            if any(itm.state() != constants.BudgetLineItemState.PENDING for itm in self):
                raise AssertionError("Some budget items are not pending")
            super(BudgetLineItem.QuerySet, self).delete()

        def filter_active(self, date=None):
            if date is None:
                date = utils.dates_helper.local_today()
            return (
                self.exclude(end_date__lt=date)
                .filter(start_date__lte=date)
                .annotate(
                    local_base_media_spend_sum=Sum("statements__local_base_media_spend_nano"),
                    local_base_data_spend_sum=Sum("statements__local_base_data_spend_nano"),
                )
                .exclude(
                    amount__lte=core.features.bcm.helpers.Round(
                        core.features.bcm.helpers.Coalesce("local_base_media_spend_sum") * 1e-9
                        + core.features.bcm.helpers.Coalesce("local_base_data_spend_sum") * 1e-9
                    )
                )
            )

        def filter_overlapping(self, start_date, end_date):
            return self.filter(
                (Q(start_date__gte=start_date) & Q(start_date__lte=end_date))
                | (Q(end_date__gte=start_date) & Q(end_date__lte=end_date))
                | (Q(start_date__lte=start_date) & Q(end_date__gte=end_date))
            )

        def filter_today(self):
            current_date = utils.dates_helper.local_today()
            return self.filter_overlapping(current_date, current_date)

        def filter_present_and_future(self):
            current_date = utils.dates_helper.local_today()
            future_date = datetime.date(2222, 1, 1)
            return self.filter_overlapping(current_date, future_date)

        def annotate_spend_data(self):
            return self.annotate(
                spend_data_b_media=Sum("statements__" + dailystatement.B_MEDIA_FIELD),
                spend_data_b_data=Sum("statements__" + dailystatement.B_DATA_FIELD),
                spend_data_e_media=Sum("statements__" + dailystatement.E_MEDIA_FIELD),
                spend_data_e_data=Sum("statements__" + dailystatement.E_DATA_FIELD),
                spend_data_service_fee=Sum("statements__service_fee_nano"),
                spend_data_license_fee=Sum("statements__license_fee_nano"),
                spend_data_margin=Sum("statements__margin_nano"),
                spend_data_et_total=Sum(sum(F("statements__" + field) for field in dailystatement.ET_TOTALS_FIELDS)),
                spend_data_etf_total=Sum(sum(F("statements__" + field) for field in dailystatement.ETF_TOTALS_FIELDS)),
                spend_data_etfm_total=Sum(
                    sum(F("statements__" + field) for field in dailystatement.ETFM_TOTALS_FIELDS)
                ),
                spend_data_local_b_media=Sum("statements__" + dailystatement.LOCAL_B_MEDIA_FIELD),
                spend_data_local_b_data=Sum("statements__" + dailystatement.LOCAL_B_DATA_FIELD),
                spend_data_local_e_media=Sum("statements__" + dailystatement.LOCAL_E_MEDIA_FIELD),
                spend_data_local_e_data=Sum("statements__" + dailystatement.LOCAL_E_DATA_FIELD),
                spend_data_local_service_fee=Sum("statements__local_service_fee_nano"),
                spend_data_local_license_fee=Sum("statements__local_license_fee_nano"),
                spend_data_local_margin=Sum("statements__local_margin_nano"),
                spend_data_local_et_total=Sum(
                    sum(F("statements__" + field) for field in dailystatement.LOCAL_ET_TOTALS_FIELDS)
                ),
                spend_data_local_etf_total=Sum(
                    sum(F("statements__" + field) for field in dailystatement.LOCAL_ETF_TOTALS_FIELDS)
                ),
                spend_data_local_etfm_total=Sum(
                    sum(F("statements__" + field) for field in dailystatement.LOCAL_ETFM_TOTALS_FIELDS)
                ),
            )
