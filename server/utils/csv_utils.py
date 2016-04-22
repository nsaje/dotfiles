#!/usr/bin/env python
# -*- coding: utf-8 -*-

import StringIO
import unicodecsv
import xlsxwriter


def convert_to_xls(csv_str, encoding='utf-8'):
    '''
    Convert CSV file in a string to xlsx
    '''

    # unicodecsv file reads and decodes byte strings
    lines = csv_str.encode('utf-8').strip().split('\n')
    reader = unicodecsv.reader(lines, encoding=encoding)

    # Create a workbook and add a worksheet.
    buf = StringIO.StringIO()
    workbook = xlsxwriter.Workbook(buf)
    worksheet = workbook.add_worksheet()
    # Iterate over the data and write it out row by row.
    for row, line in enumerate(reader):
        for col, el in enumerate(line):
            worksheet.write(row, col, el)
    workbook.close()
    return buf.getvalue()
