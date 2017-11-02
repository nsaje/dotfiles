#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cStringIO as StringIO
import unicodecsv


FORMULA_SYMBOLS = ('@', '+', '-', '=')


def tuplelist_to_csv(data):
    out = StringIO.StringIO()
    csv_file = unicodecsv.writer(
        out, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)
    for row in data:
        csv_file.writerow(_sanitize_list_row(row))
    return out.getvalue()


def dictlist_to_csv(fields, rows, writeheader=True):
    out = StringIO.StringIO()
    writer = unicodecsv.DictWriter(
        out, fields, encoding='utf-8', dialect='excel', quoting=unicodecsv.QUOTE_ALL)

    if writeheader:
        writer.writeheader()

    for row in rows:
        writer.writerow(_sanitize_dict_row(row))

    return out.getvalue()


def _sanitize_list_row(row):
    return [_prepend_if_formula(el) for el in row]


def _sanitize_dict_row(row):
    transformed = {}
    for key, value in row.items():
        transformed[key] = _prepend_if_formula(value)
    return transformed


def _prepend_if_formula(value):
    # NOTE: aims to prevent malicious input performing formula injection in spredsheet applications
    # See https://www.contextis.com/blog/comma-separated-vulnerabilities
    if value and unicode(value).startswith(FORMULA_SYMBOLS):
        value = "'" + unicode(value)
    return value
