import unicodecsv
from xlsxwriter import Workbook
import StringIO

import reports.api
import reports.api_helpers


def generate_rows(dimensions, start_date, end_date, user, **kwargs):
    ordering = ['date'] if 'date' in dimensions else []
    data = reports.api_helpers.filter_by_permissions(reports.api.query(
        start_date,
        end_date,
        dimensions,
        ordering,
        **kwargs
    ), user)

    return data


def get_csv_content(fieldnames, data, title_text=None, start_date=None, end_date=None):
    output = StringIO.StringIO()
    need_nl = False
    if title_text is not None:
        output.write('# {0}\n'.format(title_text))
        need_nl = True
    if start_date is not None and end_date is not None:
        output.write('# Start date {0}\n'.format(start_date.strftime('%m/%d/%Y')))
        output.write('# End date {0}\n'.format(end_date.strftime('%m/%d/%Y')))
        need_nl = True
    if need_nl:
        output.write('\n')

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


def get_excel_content(sheets_data, start_date=None, end_date=None):
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
            data=[_get_excel_values_list(item, columns) for item in data],
            start_date=start_date,
            end_date=end_date
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


def _create_excel_worksheet(workbook, name, columns, data, start_date=None, end_date=None):
    worksheet = workbook.add_worksheet(name)

    row_ix = 0
    if start_date is not None and end_date is not None:
        worksheet.write(row_ix, 0, name)
        row_ix += 1
        worksheet.write(row_ix, 0, 'Start date {0}'.format(start_date.strftime('%m/%d/%Y')))
        row_ix += 1
        worksheet.write(row_ix, 0, 'End date {0}'.format(end_date.strftime('%m/%d/%Y')))
        row_ix += 2

    for index, col in enumerate(columns):
        worksheet.set_column(
            index,
            index,
            col['width'] if 'width' in col else None,
            col['format'] if 'format' in col else None
        )

        worksheet.write(row_ix, index, col['name'])

    worksheet.freeze_panes(row_ix + 1, 0)  # freeze the first row

    for index, item in enumerate(data):
        _write_excel_row(worksheet, index + row_ix + 1, item)
