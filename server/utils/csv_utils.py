#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv
import io as StringIO

import django.http

FORMULA_SYMBOLS = ("@", "+", "-", "=")


def tuplelist_to_csv(data, dialect="excel"):
    out = StringIO.StringIO()
    csv_file = csv.writer(out, dialect=dialect, quoting=csv.QUOTE_ALL)
    for row in data:
        csv_file.writerow(_sanitize_list_row(row))
    return out.getvalue()


def dictlist_to_csv(fields, rows, writeheader=True, quoting=csv.QUOTE_ALL, delimiter=None):
    out = StringIO.StringIO()
    fmtparams = {"quoting": quoting}
    if delimiter:
        fmtparams["delimiter"] = delimiter
    writer = csv.DictWriter(out, fields, dialect="excel", **fmtparams)

    if writeheader:
        writer.writeheader()

    for row in rows:
        writer.writerow(_sanitize_dict_row(row))

    return out.getvalue()


def _sanitize_list_row(row):
    return [_prepend_if_formula(el) for el in row]


def _sanitize_dict_row(row):
    transformed = {}
    for key, value in list(row.items()):
        transformed[key] = _prepend_if_formula(value)
    return transformed


def _prepend_if_formula(value):
    # NOTE: aims to prevent malicious input performing formula injection in spredsheet applications
    # See https://www.contextis.com/blog/comma-separated-vulnerabilities
    if value and str(value).startswith(FORMULA_SYMBOLS):
        value = "'" + str(value)
    return value


def insert_csv_row(data, row_title, row_data):
    data.append((row_title,))
    data.append(tuple(row_data))
    data.append((None,))
    return data


def insert_csv_paragraph(data, paragraph_title, paragraph_data, key, value):
    data.append((paragraph_title,))
    for pd in paragraph_data:
        if pd[value]:
            data.append((pd[key], pd[value]))
    data.append((None,))
    return data


def create_csv_response(data="", filename="", status_code=200):
    content_type = "text/csv; name={}.csv".format(filename)
    response = django.http.HttpResponse(data, content_type=content_type, status=status_code)
    response["Content-Disposition"] = "attachment; filename={}.csv".format(filename)
    return response
