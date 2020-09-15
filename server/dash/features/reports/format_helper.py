import datetime
from decimal import Decimal

import dash.constants
from stats import constants

FORMAT_1_DECIMAL = []
FORMAT_2_DECIMALS = []
FORMAT_3_DECIMALS = []
FORMAT_4_DECIMALS = [
    "pv_per_visit",
    "data_cost",
    "media_cost",
    "b_media_cost",
    "b_data_cost",
    "e_media_cost",
    "e_data_cost",
    "service_fee",
    "license_fee",
    "margin",
    "avg_tos",
    "ctr",
    "at_cost",
    "bt_cost",
    "et_cost",
    "etf_cost",
    "etfm_cost",
    "yesterday_at_cost",
    "yesterday_etfm_cost",
    "etfm_cpc",
    "etfm_cpm",
    "video_etfm_cpv",
    "video_etfm_cpcv",
    "avg_etfm_cost_per_minute",
    "avg_etfm_cost_per_non_bounced_visit",
    "avg_etfm_cost_per_pageview",
    "avg_etfm_cost_for_new_visitor",
    "avg_etfm_cost_per_visit",
    "avg_etfm_cost_per_unique_user",
    "etfm_mrc50_vcpm",
    "etfm_mrc100_vcpm",
    "etfm_vast4_vcpm",
]
FORMAT_DIVIDE_100 = ["percent_new_users", "bounce_rate", "ctr", "click_discrepancy"]
FORMAT_EMPTY_TO_0 = [
    "media_cost",
    "b_media_cost",
    "e_media_cost",
    "data_cost",
    "b_data_cost",
    "e_data_cost",
    "service_fee",
    "license_fee",
    "margin",
    "at_cost",
    "bt_cost",
    "et_cost",
    "etf_cost",
    "etfm_cost",
    "yesterday_at_cost",
    "yesterday_etfm_cost",
    "etfm_cpc",
    "etfm_cpm",
    "clicks",
    "impressions",
    "ctr",
]
FORMAT_HASH = ["image_hash"]


formatters = {}


def get_dash_constant_formatter(constant_class):
    def format_(value):
        return constant_class.get_name(value)

    return format_


def format_values(rows, columns, csv_decimal_separator):
    if len(rows) <= 0:
        return rows
    for column in columns:
        if "avg_etfm_cost_per" in column:
            formatter = format_2_decimal
        else:
            formatter = formatters.get(column)

        if not formatter:
            sample_value = rows[0].get(column)
            if sample_value and isinstance(sample_value, Decimal) or isinstance(sample_value, float):
                formatter = format_4_decimal

        if column in FORMAT_EMPTY_TO_0:
            empty_value = 0
        else:
            empty_value = ""

        if (
            formatter in [format_1_decimal, format_2_decimal, format_3_decimal, format_4_decimal]
            and csv_decimal_separator
        ):
            formatter = fix_decimal_separator(formatter, csv_decimal_separator)

        for row in rows:
            try:
                # delivery dimension should have UNKNOWNs instead of empty_value
                if not row[column] and column not in constants.DeliveryDimension._ALL:
                    row[column] = empty_value
                elif formatter is not None:
                    row[column] = formatter(row[column])
            except KeyError:
                pass


def format_date(value: datetime.date) -> str:
    return value.strftime("%Y-%m-%d")


def format_week(value: datetime.date) -> str:
    return "Week {} - {}".format(value.isoformat(), (value + datetime.timedelta(days=6)).isoformat())


def format_month(value: datetime.date) -> str:
    return value.strftime("%Y-%m-01")


def format_1_decimal(value):
    return "{:.1f}".format(Decimal(value or 0))


def format_2_decimal(value):
    return "{:.2f}".format(Decimal(value or 0))


def format_3_decimal(value):
    return "{:.3f}".format(Decimal(value or 0))


def format_4_decimal(value):
    return "{:.4f}".format(Decimal(value or 0))


def format_hash(value):
    return "#{}".format(value)


def format_percentages(value):
    return "{:.4f}".format(value / 100)


def fix_decimal_separator(formatter, csv_decimal_separator):
    def format_(value):
        return str(formatter(value)).replace(".", csv_decimal_separator)

    return format_


formatters[constants.TimeDimension.DAY] = format_date
formatters[constants.TimeDimension.WEEK] = format_week
formatters[constants.TimeDimension.MONTH] = format_month

formatters[constants.DeliveryDimension.DEVICE] = get_dash_constant_formatter(dash.constants.DeviceType)
formatters[constants.DeliveryDimension.DEVICE_OS] = get_dash_constant_formatter(dash.constants.OperatingSystem)
formatters[constants.DeliveryDimension.DEVICE_OS_VERSION] = get_dash_constant_formatter(
    dash.constants.OperatingSystemVersion
)
formatters[constants.DeliveryDimension.ENVIRONMENT] = get_dash_constant_formatter(dash.constants.Environment)
formatters[constants.DeliveryDimension.ZEM_PLACEMENT_TYPE] = get_dash_constant_formatter(
    dash.constants.ZemPlacementType
)
formatters[constants.DeliveryDimension.VIDEO_PLAYBACK_METHOD] = get_dash_constant_formatter(
    dash.constants.VideoPlaybackMethod
)
formatters[constants.DeliveryDimension.AGE] = get_dash_constant_formatter(dash.constants.Age)
formatters[constants.DeliveryDimension.GENDER] = get_dash_constant_formatter(dash.constants.Gender)
formatters[constants.DeliveryDimension.AGE_GENDER] = get_dash_constant_formatter(dash.constants.AgeGender)

for column in FORMAT_DIVIDE_100:
    formatters[column] = format_percentages
for column in FORMAT_1_DECIMAL:
    formatters[column] = format_1_decimal
for column in FORMAT_2_DECIMALS:
    formatters[column] = format_2_decimal
for column in FORMAT_3_DECIMALS:
    formatters[column] = format_3_decimal
for column in FORMAT_4_DECIMALS:
    formatters[column] = format_4_decimal
for column in FORMAT_HASH:
    formatters[column] = format_hash
