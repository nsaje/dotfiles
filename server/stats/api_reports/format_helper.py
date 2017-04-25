import datetime
from decimal import Decimal

import dash.export
from stats import constants

formatters = {}


def format_values(rows):
    if len(rows) <= 0:
        return rows
    for column in rows[0].iterkeys():
        if 'avg_cost_per' in column:
            formatter = format_2_decimal
        else:
            formatter = formatters.get(column)

        if column in dash.export.FORMAT_EMPTY_TO_0:
            empty_value = 0
        else:
            empty_value = ''

        for row in rows:
            try:
                if not row[column]:
                    row[column] = empty_value
                elif formatter is not None:
                    row[column] = formatter(row[column])
            except KeyError:
                pass


def format_date(value):
    return value.strftime('%Y-%m-%d')


def format_week(value):
    return "Week {} - {}".format(
        value.isoformat(), (value + datetime.timedelta(days=6)).isoformat())


def format_month(value):
    return "Month {}/{}".format(value.month, value.year)


def format_1_decimal(value):
    return '{:.1f}'.format(Decimal(value or 0))


def format_2_decimal(value):
    return '{:.2f}'.format(Decimal(value or 0))


def format_3_decimal(value):
    return '{:.3f}'.format(Decimal(value or 0))


def format_4_decimal(value):
    return '{:.4f}'.format(Decimal(value or 0))


def format_hash(value):
    return '#{}'.format(value)


def format_percentages(value):
    return '{:.4f}'.format(value / 100)


formatters[constants.TimeDimension.DAY] = format_date
formatters[constants.TimeDimension.WEEK] = format_week
formatters[constants.TimeDimension.MONTH] = format_month

for column in dash.export.FORMAT_DIVIDE_100:
    formatters[column] = format_percentages
for column in dash.export.FORMAT_1_DECIMAL:
    formatters[column] = format_1_decimal
for column in dash.export.FORMAT_2_DECIMALS:
    formatters[column] = format_2_decimal
for column in dash.export.FORMAT_3_DECIMALS:
    formatters[column] = format_3_decimal
for column in dash.export.FORMAT_4_DECIMALS:
    formatters[column] = format_4_decimal
for column in dash.export.FORMAT_HASH:
    formatters[column] = format_hash
