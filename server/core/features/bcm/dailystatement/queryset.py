from django.db.models import F
from django.db.models import QuerySet
from django.db.models import Sum

import utils.converters
import utils.dates_helper

B_MEDIA_FIELD = "base_media_spend_nano"
B_DATA_FIELD = "base_data_spend_nano"
E_MEDIA_FIELD = "media_spend_nano"
E_DATA_FIELD = "data_spend_nano"
ET_TOTALS_FIELDS = ["base_media_spend_nano", "base_data_spend_nano", "service_fee_nano"]
ETF_TOTALS_FIELDS = ["base_media_spend_nano", "base_data_spend_nano", "service_fee_nano", "license_fee_nano"]
ETFM_TOTALS_FIELDS = [
    "base_media_spend_nano",
    "base_data_spend_nano",
    "service_fee_nano",
    "license_fee_nano",
    "margin_nano",
]

LOCAL_B_MEDIA_FIELD = "local_base_media_spend_nano"
LOCAL_B_DATA_FIELD = "local_base_data_spend_nano"
LOCAL_E_MEDIA_FIELD = "local_media_spend_nano"
LOCAL_E_DATA_FIELD = "local_data_spend_nano"
LOCAL_ET_TOTALS_FIELDS = ["local_base_media_spend_nano", "local_base_data_spend_nano", "local_service_fee_nano"]
LOCAL_ETF_TOTALS_FIELDS = [
    "local_base_media_spend_nano",
    "local_base_data_spend_nano",
    "local_service_fee_nano",
    "local_license_fee_nano",
]
LOCAL_ETFM_TOTALS_FIELDS = [
    "local_base_media_spend_nano",
    "local_base_data_spend_nano",
    "local_service_fee_nano",
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
                base_media=Sum(B_MEDIA_FIELD),
                base_data=Sum(B_DATA_FIELD),
                media=Sum(E_MEDIA_FIELD),
                data=Sum(E_DATA_FIELD),
                service_fee=Sum("service_fee_nano"),
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
                base_media=Sum(LOCAL_B_MEDIA_FIELD),
                base_data=Sum(LOCAL_B_DATA_FIELD),
                media=Sum(LOCAL_E_MEDIA_FIELD),
                data=Sum(LOCAL_E_DATA_FIELD),
                service_fee=Sum("local_service_fee_nano"),
                license_fee=Sum("local_license_fee_nano"),
                margin=Sum("local_margin_nano"),
                et_total=Sum(sum(F(field) for field in ET_TOTALS_FIELDS)),
                etf_total=Sum(sum(F(field) for field in LOCAL_ETF_TOTALS_FIELDS)),
                etfm_total=Sum(sum(F(field) for field in LOCAL_ETFM_TOTALS_FIELDS)),
            ).items()
        }
