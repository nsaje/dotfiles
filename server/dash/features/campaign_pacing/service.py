import dataclasses
import datetime
from decimal import Decimal
from typing import Dict
from typing import Sequence

import newrelic.agent
from django.db.models import F
from django.db.models import Q
from django.db.models import Sum

import core.features.bcm
import core.models
import etl.materialization_run
import utils.converters
import utils.dates_helper

PACING_WINDOW_1_DAY = 1
PACING_WINDOW_3_DAYS = 3
PACING_WINDOW_7_DAYS = 7


@dataclasses.dataclass
class PacingWindowData:
    start_date: datetime.datetime
    end_date: datetime.datetime
    total_budget: Decimal
    attributed_spend: Decimal
    pacing: Decimal


PacingData = Dict[int, PacingWindowData]


class CampaignPacing(object):
    def __init__(self, campaign: core.models.Campaign) -> None:
        self.yesterday_data_complete: bool = etl.materialization_run.etl_data_complete_for_date(
            utils.dates_helper.local_yesterday()
        )
        target_date: datetime.datetime = utils.dates_helper.local_today()
        pacing_data: PacingData = self._init_pacing_data(target_date)
        budgets: Sequence[core.features.bcm.BudgetLineItem] = self._prepare_budgets(target_date, campaign, pacing_data)
        pacing_data = self._calculate_spend(budgets, pacing_data)
        self.data: PacingData = self._calculate_pacing(pacing_data)

    def _init_pacing_data(self, target_date: datetime.datetime) -> PacingData:
        pacing_data: PacingData = {}

        for window in [PACING_WINDOW_1_DAY, PACING_WINDOW_3_DAYS, PACING_WINDOW_7_DAYS]:
            pacing_data[window] = PacingWindowData(
                start_date=target_date - datetime.timedelta(window),
                end_date=target_date - datetime.timedelta(1),
                total_budget=Decimal("0"),
                attributed_spend=Decimal("0"),
                pacing=Decimal("0"),
            )

        return pacing_data

    @newrelic.agent.function_trace()
    def _prepare_budgets(
        self, target_date: datetime.datetime, campaign: core.models.Campaign, pacing_data: PacingData
    ) -> Sequence[core.features.bcm.BudgetLineItem]:
        min_start_date = pacing_data[PACING_WINDOW_7_DAYS].start_date
        max_end_date = pacing_data[PACING_WINDOW_7_DAYS].end_date

        budgets = core.features.bcm.BudgetLineItem.objects.exclude(
            start_date__gt=max_end_date, end_date__lt=min_start_date
        ).filter(campaign=campaign)

        for window, data in pacing_data.items():
            window_spend_key = "window_spend_" + str(window)
            initial_spend_key = "initial_spend_" + str(window)
            aggregation = sum(
                F("statements__" + field) for field in core.features.bcm.dailystatement.LOCAL_ETFM_TOTALS_FIELDS
            )

            budgets = budgets.annotate(
                **{
                    window_spend_key: Sum(
                        aggregation,
                        filter=Q(statements__date__lt=target_date)
                        & Q(statements__date__gte=data.start_date)
                        & Q(statements__date__lte=data.end_date),
                    ),
                    initial_spend_key: Sum(
                        aggregation,
                        filter=Q(statements__date__lt=target_date) & Q(statements__date__lt=data.start_date),
                    ),
                }
            )

        return budgets

    def _calculate_spend(
        self, budgets: Sequence[core.features.bcm.BudgetLineItem], pacing_data: PacingData
    ) -> PacingData:
        for window, data in pacing_data.items():
            total_budget = Decimal("0")
            spend = Decimal("0")

            for budget in budgets:
                overlap_start_date, overlap_end_date = budget.get_overlap(data.start_date, data.end_date)
                if not overlap_start_date or not overlap_end_date:
                    continue

                spend += utils.converters.nano_to_decimal(getattr(budget, "window_spend_" + str(window))) or Decimal(
                    "0"
                )
                initial_spend = utils.converters.nano_to_decimal(
                    getattr(budget, "initial_spend_" + str(window))
                ) or Decimal("0")

                window_budget = budget.allocated_amount() - initial_spend

                if budget.end_date > data.end_date:
                    budget_pacing_days = (overlap_end_date - overlap_start_date).days + 1
                    budget_remaining_days = (budget.end_date - overlap_start_date).days + 1
                    window_budget = window_budget / Decimal(budget_remaining_days) * budget_pacing_days

                total_budget += window_budget

            pacing_data[window].total_budget = total_budget
            pacing_data[window].attributed_spend = spend

        return pacing_data

    def _calculate_pacing(self, pacing_data: PacingData) -> PacingData:
        for window, data in pacing_data.items():
            if data.total_budget:
                pacing_data[window].pacing = data.attributed_spend / data.total_budget * Decimal(100)

        return pacing_data
