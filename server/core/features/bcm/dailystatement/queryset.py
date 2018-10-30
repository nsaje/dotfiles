from django.db.models import F
from django.db.models import QuerySet
from django.db.models import Sum

import utils.converters
import utils.dates_helper

ET_TOTALS_FIELDS = ["media_spend_nano", "data_spend_nano"]
ETF_TOTALS_FIELDS = ["media_spend_nano", "data_spend_nano", "license_fee_nano"]
ETFM_TOTALS_FIELDS = ["media_spend_nano", "data_spend_nano", "license_fee_nano", "margin_nano"]

LOCAL_ET_TOTALS_FIELDS = ["local_media_spend_nano", "local_data_spend_nano"]
LOCAL_ETF_TOTALS_FIELDS = ["local_media_spend_nano", "local_data_spend_nano", "local_license_fee_nano"]
LOCAL_ETFM_TOTALS_FIELDS = [
    "local_media_spend_nano",
    "local_data_spend_nano",
    "local_license_fee_nano",
    "local_margin_nano",
]


class BudgetDailyStatementQuerySet(QuerySet):
    def filter_mtd(self):
        current_date = utils.dates_helper.local_today()
        start_date = current_date.replace(day=1)

        return self.filter(date__gte=start_date, date__lte=current_date)

    def calculate_spend_data(self):
        return {
            key: utils.converters.nano_to_decimal(spend or 0)
            for key, spend in self.aggregate(
                media=Sum("media_spend_nano"),
                data=Sum("data_spend_nano"),
                license_fee=Sum("license_fee_nano"),
                margin=Sum("margin_nano"),
                et_total=Sum(sum(F(field) for field in ET_TOTALS_FIELDS)),
                etf_total=Sum(sum(F(field) for field in ETF_TOTALS_FIELDS)),
                etfm_total=Sum(sum(F(field) for field in ETFM_TOTALS_FIELDS)),
            ).items()
        }

    def calculate_local_spend_data(self):
        return {
            key: utils.converters.nano_to_decimal(spend or 0)
            for key, spend in self.aggregate(
                media=Sum("local_media_spend_nano"),
                data=Sum("local_data_spend_nano"),
                license_fee=Sum("local_license_fee_nano"),
                margin=Sum("local_margin_nano"),
                et_total=Sum(sum(F(field) for field in LOCAL_ET_TOTALS_FIELDS)),
                etf_total=Sum(sum(F(field) for field in LOCAL_ETF_TOTALS_FIELDS)),
                etfm_total=Sum(sum(F(field) for field in LOCAL_ETFM_TOTALS_FIELDS)),
            ).items()
        }
