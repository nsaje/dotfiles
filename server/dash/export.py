import unicodecsv
from xlsxwriter import Workbook
import StringIO

import reports.api


def generate_rows(dimensions, start_date, end_date, user, **kwargs):
    ordering = ['date'] if 'date' in dimensions else []
    data = reports.api.filter_by_permissions(reports.api.query(
        start_date,
        end_date,
        dimensions,
        ordering,
        **kwargs
    ), user)

    return data


def get_csv_content(fieldnames, data):
    output = StringIO.StringIO()
    writer = unicodecsv.DictWriter(output, fieldnames, encoding='utf-8', dialect='excel')

    # header
    writer.writerow(fieldnames)

    for item in data:
        # Format
        row = {}
        for key in fieldnames:
            value = item[key]

            if not value and key in ['cost', 'cpc', 'clicks', 'impressions', 'ctr']:
                value = 0

            if key == 'ctr':
                value = '{:.2f}'.format(value)

            row[key] = value

        writer.writerow(row)

    return output.getvalue()


def get_excel_content(sheets_data):
    output = StringIO.StringIO()
    workbook = Workbook(output, {'strings_to_urls': False})

    format_date = workbook.add_format({'num_format': u'm/d/yy'})
    format_percent = workbook.add_format({'num_format': u'0.00%'})
    format_usd = workbook.add_format({'num_format': u'[$$-409]#,##0.00;-[$$-409]#,##0.00'})

    for name, columns, data in sheets_data:
        # set format
        for column in columns:
            if 'format' in column:
                format_id = column['format']

                if format_id == 'date':
                    column['format'] = format_date
                elif format_id == 'currency':
                    column['format'] = format_usd
                elif format_id == 'percent':
                    column['format'] = format_percent

        _create_excel_worksheet(
            workbook,
            name,
            columns,
            data=[_get_excel_values_list(item, columns) for item in data]
        )

    workbook.close()
    output.seek(0)

    return output.read()


def _get_excel_value(item, key):
    value = item[key]

    if not value and key in ['cost', 'cpc', 'clicks', 'impressions', 'ctr']:
        value = 0

    if key == 'ctr':
        value = value / 100

    return value


def _get_excel_values_list(item, columns):
    return [_get_excel_value(item, column['key']) for column in columns]


def _write_excel_row(worksheet, row_index, column_data):
    for column_index, column_value in enumerate(column_data):
        worksheet.write(
            row_index,
            column_index,
            column_value
        )


def _create_excel_worksheet(workbook, name, columns, data):
    worksheet = workbook.add_worksheet(name)

    for index, col in enumerate(columns):
        worksheet.set_column(
            index,
            index,
            col['width'] if 'width' in col else None,
            col['format'] if 'format' in col else None
        )

        worksheet.write(0, index, col['name'])

    worksheet.freeze_panes(1, 0)  # freeze the first row

    for index, item in enumerate(data):
        _write_excel_row(worksheet, index + 1, item)
