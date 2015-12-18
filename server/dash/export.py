import unicodecsv
from xlsxwriter import Workbook
import StringIO

from dash import models
from dash import stats_helper

import reports.api
import reports.api_contentads
import reports.api_helpers

from utils.sort_helper import sort_results


def generate_rows(dimensions, start_date, end_date, user, ignore_diff_rows=False, conversion_goals=None, **kwargs):
    ordering = ['date'] if 'date' in dimensions else []

    if 'content_ad' in dimensions:
        return _generate_content_ad_rows(
            dimensions,
            start_date,
            end_date,
            user,
            ordering,
            ignore_diff_rows,
            conversion_goals,
            **kwargs
        )

    if user.has_perm('zemauth.can_see_redshift_postclick_statistics') and 'article' not in dimensions:
        return stats_helper.get_stats_with_conversions(
            user,
            start_date,
            end_date,
            breakdown=dimensions,
            order=ordering,
            ignore_diff_rows=ignore_diff_rows,
            conversion_goals=conversion_goals,
            constraints=kwargs
        )

    return reports.api_helpers.filter_by_permissions(reports.api.query(
        start_date,
        end_date,
        dimensions,
        ordering,
        ignore_diff_rows=ignore_diff_rows,
        **kwargs
    ), user)


def _get_content_ads(constraints):
    sources = None
    fields = {}

    for key in constraints:
        if key == 'source':
            sources = constraints[key]
        elif key == 'campaign':
            fields['ad_group__campaign'] = constraints[key]
        else:
            fields[key] = constraints[key]

    content_ads = models.ContentAd.objects.filter(**fields).select_related('batch')

    if sources is not None:
        content_ads = content_ads.filter_by_sources(sources)

    return {c.id: c for c in content_ads}


def _generate_content_ad_rows(dimensions, start_date, end_date, user, ordering, ignore_diff_rows, conversion_goals, **constraints):
    content_ads = _get_content_ads(constraints)

    stats = stats_helper.get_content_ad_stats_with_conversions(
        user,
        start_date,
        end_date,
        breakdown=dimensions,
        ignore_diff_rows=ignore_diff_rows,
        conversion_goals=conversion_goals,
        constraints=constraints
    )

    for stat in stats:
        content_ad = content_ads[stat['content_ad']]
        stat['title'] = content_ad.title
        stat['url'] = content_ad.url
        stat['image_url'] = content_ad.get_image_url()
        stat['uploaded'] = content_ad.created_dt.date()

    return sort_results(stats, ordering)


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
            value = item.get(key)

            if not value and key in ['data_cost', 'cost', 'cpc', 'clicks', 'impressions', 'ctr',
                                     'visits', 'pageviews', 'e_media_cost', 'media_cost', 
                                     'e_data_cost', 'total_cost', 'billing_cost', 'license_fee']:
                value = 0

            if value and key in ['ctr', 'click_discrepancy', 'percent_new_users', 'bounce_rate', 'pv_per_visit', 'avg_tos']:
                value = '{:.2f}'.format(value)

            row[key] = value

        writer.writerow(row)

    return output.getvalue()


def get_excel_content(sheets_data, start_date=None, end_date=None):
    output = StringIO.StringIO()
    workbook = Workbook(output, {'strings_to_urls': False})

    format_date = workbook.add_format({'num_format': u'm/d/yy'})
    format_percent = workbook.add_format({'num_format': u'0.00%'})
    format_decimal = workbook.add_format({'num_format': u'0.00'})
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
                elif format_id == 'decimal':
                    column['format'] = format_decimal

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
    value = item.get(key)

    if not value and key in ['data_cost', 'cost', 'cpc', 'clicks', 'impressions',
                             'ctr', 'visits', 'pageviews', 'e_media_cost', 'media_cost',
                             'e_data_cost', 'total_cost', 'billing_cost', 'license_fee']:
        value = 0

    if value and key in ['ctr', 'click_discrepancy', 'percent_new_users', 'bounce_rate']:
        value /= 100

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
