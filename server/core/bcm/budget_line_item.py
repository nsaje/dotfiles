# -*- coding: utf-8 -*-
import datetime
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db import transaction
from django.db.models import Sum, Q, F
from django.forms.models import model_to_dict

import utils.demo_anonymizer
import utils.string_helper
import utils.dates_helper
from dash import constants
from utils import converters
from utils import lc_helper
from utils import validation_helper

import core.bcm
import core.bcm.helpers
import core.common
import core.history
import core.multicurrency
from . import dailystatement
from . import exceptions
from . import bcm_slack

import automation.campaignstop


EXCLUDE_ACCOUNTS_LOW_AMOUNT_CHECK = (431, 305)

SKIP_AMOUNT_VALIDATION_CREDIT_IDS = [1251]


class BudgetLineItemManager(core.common.QuerySetManager):
    @transaction.atomic
    def create(
        self,
        request,
        campaign,
        credit,
        start_date,
        end_date,
        amount,
        margin=None,
        comment=None,
    ):
        core.common.entity_limits.enforce(
            BudgetLineItem.objects.filter(campaign=campaign), campaign.account_id
        )
        item = BudgetLineItem(
            campaign=campaign,
            credit=credit,
            start_date=start_date,
            end_date=end_date,
            amount=amount,
        )
        if margin is not None:
            item.margin = margin
        if comment is not None:
            item.comment = comment

        item.clean_start_date()
        item.clean_end_date()
        item.save(request=request, action_type=constants.HistoryActionType.CREATE)

        bcm_slack.log_to_slack(
            campaign.account_id,
            bcm_slack.SLACK_NEW_BUDGET_MSG.format(
                budget_id=item.pk,
                url=bcm_slack.CAMPAIGN_URL.format(campaign.id),
                campaign_id=campaign.id,
                campaign_name=campaign.get_long_name(),
                amount=item.amount,
                currency_symbol=core.multicurrency.get_currency_symbol(
                    item.credit.currency
                ),
                end_date=item.end_date,
            ),
        )

        return item


class BudgetLineItem(core.common.FootprintModel, core.history.HistoryMixinOld):
    class Meta:
        app_label = "dash"

    history_fields = [
        "start_date",
        "end_date",
        "amount",
        "freed_cc",
        "margin",
        "comment",
    ]

    _demo_fields = {"comment": lambda: "Monthly budget"}
    campaign = models.ForeignKey(
        "Campaign", related_name="budgets", on_delete=models.PROTECT
    )
    credit = models.ForeignKey(
        "CreditLineItem", related_name="budgets", on_delete=models.PROTECT
    )
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
            currency_symbol=core.multicurrency.get_currency_symbol(
                self.credit.currency
            ),
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
        currency_symbol = core.multicurrency.get_currency_symbol(self.credit.currency)
        if prop_name == "amount" and value is not None:
            value = lc_helper.format_currency(value, places=2, curr=currency_symbol)
        elif prop_name == "freed_cc" and value is not None:
            value = lc_helper.format_currency(
                Decimal(value) * converters.CC_TO_DECIMAL_CURRENCY,
                places=2,
                curr=currency_symbol,
            )
        elif prop_name == "flat_fee_cc":
            value = lc_helper.format_currency(
                Decimal(value) * converters.CC_TO_DECIMAL_CURRENCY,
                places=2,
                curr=currency_symbol,
            )
        elif prop_name == "margin" and value is not None:
            value = "{}%".format(
                utils.string_helper.format_decimal(Decimal(value) * 100, 2, 3)
            )
        elif prop_name == "comment":
            value = value or ""
        return value

    def get_settings_dict(self):
        return {
            history_key: getattr(self, history_key)
            for history_key in self.history_fields
        }

    @transaction.atomic
    def update(self, request, **updates):
        start_date = updates.get("start_date")
        if start_date:
            self.start_date = start_date
            self.clean_start_date()
        end_date = updates.get("end_date")
        if end_date:
            self.end_date = end_date
            self.clean_end_date()
        amount = updates.get("amount")
        if amount:
            self.amount = amount
        self.save(
            request=request, action_type=constants.HistoryActionType.BUDGET_CHANGE
        )

    @transaction.atomic
    def save(self, request=None, user=None, action_type=None, *args, **kwargs):
        import core.bcm

        self.full_clean()
        if user and not self.pk:
            self.created_by = user
        elif request and not self.pk:
            self.created_by = request.user
        super(BudgetLineItem, self).save(*args, **kwargs)
        core.bcm.BudgetHistory.objects.create(
            created_by=request.user if request else user or None,
            snapshot=model_to_dict(self),
            budget=self,
        )
        self.add_to_history(request and request.user or user or None, action_type)

    def add_to_history(self, user, action_type):
        changes = self.get_model_state_changes(model_to_dict(self))
        # this is a temporary state until cleaning up of settings changes text
        if not changes and not self.post_init_newly_created:
            return None, ""

        if self.post_init_newly_created:
            changes = model_to_dict(self)

        changes, changes_text = self.construct_changes(
            "Created budget.",
            "Budget: #{}.".format(self.id) if self.id else None,
            changes,
        )
        self.campaign.write_history(
            changes_text, changes=changes, action_type=action_type, user=user
        )

    def db_state(self, date=None):
        return BudgetLineItem.objects.get(pk=self.pk).state(date=date)

    def delete(self):
        if self.db_state() != constants.BudgetLineItemState.PENDING:
            raise AssertionError("Cannot delete nonpending budgets")
        super(BudgetLineItem, self).delete()

    def get_overlap(self, start_date, end_date):
        return utils.dates_helper.get_overlap(
            self.start_date, self.end_date, start_date, end_date
        )

    def get_available_amount(self, date=None):
        if date is None:
            date = utils.dates_helper.local_today()
        local_available = self.get_local_available_amount(date)
        exchange_rate = core.multicurrency.get_exchange_rate(date, self.credit.currency)
        return local_available / exchange_rate

    def get_local_available_amount(self, date=None):
        if date is None:
            date = utils.dates_helper.local_today()
        total_spend = self.get_local_spend_data(end_date=date)["etf_total"]
        return self.allocated_amount() - total_spend

    def get_available_etfm_amount(self, date=None):
        if date is None:
            date = utils.dates_helper.local_today()
        local_available_etfm = self.get_local_available_etfm_amount(date)
        exchange_rate = core.multicurrency.get_exchange_rate(date, self.credit.currency)
        return local_available_etfm / exchange_rate

    def get_local_available_etfm_amount(self, date=None):
        if date is None:
            date = utils.dates_helper.local_today()
        total_spend = self.get_local_spend_data(end_date=date)["etfm_total"]
        return self.allocated_amount() - total_spend

    def get_local_spend_data_bcm(self):
        if self.campaign.account.uses_bcm_v2:
            return self.get_local_spend_data()["etfm_total"]
        else:
            return self.get_local_spend_data()["etf_total"]

    def get_local_available_data_bcm(self):
        if self.campaign.account.uses_bcm_v2:
            return self.get_local_available_etfm_amount()
        else:
            return self.get_local_available_amount()

    def state(self, date=None):
        if date is None:
            date = utils.dates_helper.local_today()
        if self.get_available_amount(date) <= 0:
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

    def free_inactive_allocated_assets(self):
        if self.state() != constants.BudgetLineItemState.INACTIVE:
            raise AssertionError("Budget has to be inactive to be freed.")
        amount_cc = self.amount * converters.CURRENCY_TO_CC
        spend_data = self.get_local_spend_data()
        if self.campaign.account.uses_bcm_v2:
            total_spend = spend_data["etfm_total"]
        else:
            total_spend = spend_data["etf_total"]
        total_spend = int(total_spend * converters.CURRENCY_TO_CC)

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
            statement.local_media_spend_nano
            + statement.local_data_spend_nano
            + statement.local_license_fee_nano
            + statement.local_margin_nano
        )
        return total_cc * (factor_offset + settings.BUDGET_RESERVE_FACTOR)

    def get_latest_statement(self):
        return self.statements.all().order_by("-date").first()

    def get_latest_statement_qs(self):
        latest_statement = self.get_latest_statement()
        if not latest_statement:
            return core.bcm.BudgetDailyStatement.objects.none()
        return self.statements.filter(id=latest_statement.id)

    def get_spend_data(self, date=None):
        if (date is None or date == utils.dates_helper.local_today()) and hasattr(
            self, "spend_data_media"
        ):
            return {
                "media": utils.converters.nano_to_decimal(self.spend_data_media or 0),
                "data": utils.converters.nano_to_decimal(self.spend_data_data or 0),
                "license_fee": utils.converters.nano_to_decimal(
                    self.spend_data_license_fee or 0
                ),
                "margin": utils.converters.nano_to_decimal(self.spend_data_margin or 0),
                "et_total": utils.converters.nano_to_decimal(
                    self.spend_data_et_total or 0
                ),
                "etf_total": utils.converters.nano_to_decimal(
                    self.spend_data_etf_total or 0
                ),
                "etfm_total": utils.converters.nano_to_decimal(
                    self.spend_data_etfm_total or 0
                ),
            }
        statements = self.statements
        if date:
            statements = statements.filter(date__lte=date)
        return statements.calculate_spend_data()

    def get_local_spend_data(self, start_date=None, end_date=None):
        if (
            start_date is None
            and (end_date is None or end_date == utils.dates_helper.local_today())
            and hasattr(self, "spend_data_media")
        ):
            return {
                "media": utils.converters.nano_to_decimal(
                    self.spend_data_local_media or 0
                ),
                "data": utils.converters.nano_to_decimal(
                    self.spend_data_local_data or 0
                ),
                "license_fee": utils.converters.nano_to_decimal(
                    self.spend_data_local_license_fee or 0
                ),
                "margin": utils.converters.nano_to_decimal(
                    self.spend_data_local_margin or 0
                ),
                "et_total": utils.converters.nano_to_decimal(
                    self.spend_data_local_et_total or 0
                ),
                "etf_total": utils.converters.nano_to_decimal(
                    self.spend_data_local_etf_total or 0
                ),
                "etfm_total": utils.converters.nano_to_decimal(
                    self.spend_data_local_etfm_total or 0
                ),
            }
        statements = self.statements
        if start_date:
            statements = statements.filter(date__gte=start_date)
        if end_date:
            statements = statements.filter(date__lte=end_date)
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
                raise exceptions.CanNotSetMargin(
                    "Margin can only be set on newly created budget items."
                )
            if (
                self.has_changed("start_date")
                and not db_state == constants.BudgetLineItemState.PENDING
            ):
                raise exceptions.CanNotChangeStartDate(
                    "Only pending budgets can change start date and amount."
                )
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
                raise exceptions.CanNotChangeBudget(
                    "Only pending and active budgets can change."
                )
        elif self.credit.status == constants.CreditLineItemStatus.CANCELED:
            raise exceptions.CreditCanceled(
                "Canceled credits cannot have new budget items."
            )

        validation_helper.validate_multiple(
            self.validate_start_date,
            self.validate_end_date,
            self.validate_amount,
            self.validate_credit,
            self.validate_campaign,
            self.validate_margin,
        )

    def license_fee(self):
        return self.credit.license_fee

    def validate_campaign(self):
        is_valid_account_credit = (
            self.credit.account_id
            and self.campaign.account_id == self.credit.account_id
        )
        is_valid_agency_credit = (
            self.credit.agency_id
            and self.campaign.account.agency_id == self.credit.agency_id
        )
        if not (is_valid_account_credit or is_valid_agency_credit):
            raise exceptions.CampaignHasNoCredit("Campaign has no credit.")

    def validate_credit(self):
        if self.has_changed("credit"):
            raise exceptions.CanNotChangeCredit("Credit cannot change.")
        if self.credit.status == constants.CreditLineItemStatus.PENDING:
            raise exceptions.CreditPending(
                "Cannot allocate budget from an unsigned credit."
            )
        if self.credit.currency != self.campaign.account.currency:
            raise exceptions.CurrencyInconsistent(
                "Cannot allocate budget from a credit in currency different from account's currency."
            )

        self.validate_license_fee()

    def clean_start_date(self):
        """
        Due to testing and manual adjustments budgets sometimes need
        to be created in the past. 'Date in the past' checks therefore
        aren't called automatically like 'clean_' methods usually are.
        """
        if not self.pk or self.has_changed("start_date"):
            if self.start_date < utils.dates_helper.local_today():
                raise exceptions.StartDateInThePast(
                    "Start date has to be in the future."
                )

    def clean_end_date(self):
        if not self.pk or self.has_changed("end_date"):
            if self.end_date < utils.dates_helper.local_today():
                raise exceptions.EndDateInThePast("End date has to be in the future.")

    def validate_start_date(self):
        if not self.start_date:
            return
        if self.start_date < self.credit.start_date:
            raise exceptions.StartDateInvalid(
                "Start date cannot be smaller than the credit's start date."
            )

    def validate_end_date(self):
        if not self.end_date:
            return
        if self.end_date > self.credit.end_date:
            raise exceptions.EndDateInvalid(
                "End date cannot be bigger than the credit's end date."
            )
        if self.start_date and self.start_date > self.end_date:
            raise exceptions.StartDateBiggerThanEndDate(
                "Start date cannot be bigger than the end date."
            )

    def validate_margin(self):
        if not (0 <= self.margin < 1):
            raise exceptions.MarginRangeInvalid("Margin must be between 0 and 100%.")
        if self.campaign.account.uses_bcm_v2:
            overlapping_budget_line_items = (
                BudgetLineItem.objects.filter(campaign=self.campaign)
                .exclude(margin=self.margin)
                .filter_overlapping(self.start_date, self.end_date)
            )
            if overlapping_budget_line_items.exists():
                raise exceptions.OverlappingBudgetMarginInvalid(
                    "Margin must be the same on overlapping budget line items."
                )

    def validate_license_fee(self):
        if self.campaign.account.uses_bcm_v2:
            overlapping_budget_line_items = (
                BudgetLineItem.objects.filter(campaign=self.campaign)
                .exclude(credit__license_fee=self.credit.license_fee)
                .filter_overlapping(self.start_date, self.end_date)
            )
            if overlapping_budget_line_items.exists():
                raise exceptions.OverlappingBudgets(
                    "Unable to add budget with chosen credit. Choose another credit."
                )

    def validate_amount(self):
        if (
            self.has_changed("amount")
            and self.credit.status == constants.CreditLineItemStatus.CANCELED
        ):
            raise exceptions.BudgetAmountCannotChange(
                "Canceled credit's budget amounts cannot change."
            )
        if self.amount < 0:
            raise exceptions.BudgetAmountNegative("Amount cannot be negative.")

        if self.credit_id in SKIP_AMOUNT_VALIDATION_CREDIT_IDS:
            return

        self._validate_amount_campaign_stop()

        budgets = self.credit.budgets.exclude(pk=self.pk)
        delta = (
            self.credit.effective_amount()
            - sum(b.allocated_amount() for b in budgets)
            - self.allocated_amount()
        )
        if delta < 0:
            raise exceptions.BudgetAmountExceededCreditAmount(
                "Budget exceeds the total credit amount by {currency_symbol}{delta}.".format(
                    currency_symbol=core.multicurrency.get_currency_symbol(
                        self.credit.currency
                    ),
                    delta=-delta.quantize(Decimal("1.00")),
                )
            )

    def _validate_amount_campaign_stop(self):
        prev_amount = self.previous_value("amount")
        if prev_amount is None:
            return

        if self.amount >= prev_amount:
            return
        if self.campaign.real_time_campaign_stop:
            try:
                automation.campaignstop.validate_minimum_budget_amount(
                    self, self.amount
                )
            except automation.campaignstop.CampaignStopValidationException as e:
                raise exceptions.BudgetAmountTooLow(
                    "Budget amount has to be at least {currency_symbol}{min_amount:.2f}.".format(
                        currency_symbol=core.multicurrency.get_currency_symbol(
                            self.credit.currency
                        ),
                        min_amount=e.min_amount,
                    )
                )
        else:
            acc_id = self.campaign.account_id
            if (
                self.amount < prev_amount
                and acc_id not in EXCLUDE_ACCOUNTS_LOW_AMOUNT_CHECK
            ):
                raise exceptions.CampaignStopDisabled(
                    "If campaign stop is disabled amount cannot be lowered."
                )
                return

    @classmethod
    def get_defaults_dict(cls):
        return {}

    class QuerySet(models.QuerySet):
        def delete(self):
            if any(
                itm.state() != constants.BudgetLineItemState.PENDING for itm in self
            ):
                raise AssertionError("Some budget items are not pending")
            super(BudgetLineItem.QuerySet, self).delete()

        def filter_active(self, date=None):
            if date is None:
                date = utils.dates_helper.local_today()
            return (
                self.exclude(end_date__lt=date)
                .filter(start_date__lte=date)
                .annotate(
                    local_media_spend_sum=Sum("statements__local_media_spend_nano"),
                    local_license_fee_spend_sum=Sum(
                        "statements__local_license_fee_nano"
                    ),
                    local_data_spend_sum=Sum("statements__local_data_spend_nano"),
                )
                .exclude(
                    amount__lte=core.bcm.helpers.Round(
                        core.bcm.helpers.Coalesce("local_media_spend_sum") * 1e-9
                        + core.bcm.helpers.Coalesce("local_license_fee_spend_sum")
                        * 1e-9
                        + core.bcm.helpers.Coalesce("local_data_spend_sum") * 1e-9
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

        def annotate_spend_data(self):
            return self.annotate(
                spend_data_media=Sum("statements__media_spend_nano"),
                spend_data_data=Sum("statements__data_spend_nano"),
                spend_data_license_fee=Sum("statements__license_fee_nano"),
                spend_data_margin=Sum("statements__margin_nano"),
                spend_data_et_total=Sum(
                    sum(
                        F("statements__" + field)
                        for field in dailystatement.ET_TOTALS_FIELDS
                    )
                ),
                spend_data_etf_total=Sum(
                    sum(
                        F("statements__" + field)
                        for field in dailystatement.ETF_TOTALS_FIELDS
                    )
                ),
                spend_data_etfm_total=Sum(
                    sum(
                        F("statements__" + field)
                        for field in dailystatement.ETFM_TOTALS_FIELDS
                    )
                ),
                spend_data_local_media=Sum("statements__local_media_spend_nano"),
                spend_data_local_data=Sum("statements__local_data_spend_nano"),
                spend_data_local_license_fee=Sum("statements__local_license_fee_nano"),
                spend_data_local_margin=Sum("statements__local_margin_nano"),
                spend_data_local_et_total=Sum(
                    sum(
                        F("statements__" + field)
                        for field in dailystatement.LOCAL_ET_TOTALS_FIELDS
                    )
                ),
                spend_data_local_etf_total=Sum(
                    sum(
                        F("statements__" + field)
                        for field in dailystatement.LOCAL_ETF_TOTALS_FIELDS
                    )
                ),
                spend_data_local_etfm_total=Sum(
                    sum(
                        F("statements__" + field)
                        for field in dailystatement.LOCAL_ETFM_TOTALS_FIELDS
                    )
                ),
            )
