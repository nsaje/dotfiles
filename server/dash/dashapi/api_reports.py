import copy

from dash.dashapi import augmenter
from dash.dashapi import loaders

from stats import constants
from redshiftapi.postprocess import _get_representative_dates

HIERARCHICAL_DIMENSIONS = [constants.ACCOUNT, constants.CAMPAIGN, constants.AD_GROUP, constants.CONTENT_AD]


def annotate(rows, user, breakdown, constraints, level, loader_cache=None):
    if loader_cache is None:
        loader_cache = {}

    for dimension in breakdown:
        loader = loader_cache.get(dimension, {}).get(level)
        if loader is None:
            loader_cls = loaders.get_loader_for_dimension(dimension, level)
            if loader_cls is None:
                continue

            loader = loader_cls.from_constraints(user, constraints)

            loader_cache.setdefault(dimension, {})[level] = loader

        augmenter_fn = augmenter.get_report_augmenter_for_dimension(dimension, level)
        augmenter_fn(rows, loader)


def annotate_totals(row, user, breakdown, constraints, level):
    base_dimension = constants.get_base_dimension(breakdown)

    loader_cls = loaders.get_loader_for_dimension(base_dimension, level)
    if base_dimension == constants.SOURCE:
        loader = loader_cls.from_constraints(user, constraints)
        augmenter.augment_sources_totals(row, loader)

    elif base_dimension == constants.ACCOUNT:
        loader = loader_cls.from_constraints(user, constraints)
        augmenter.augment_accounts_totals(row, loader)

    elif base_dimension == constants.CAMPAIGN:
        loader = loader_cls.from_constraints(user, constraints)
        augmenter.augment_campaigns_totals(row, loader)

    return row


def query(user, breakdown, constraints, level):
    rows = [{}]
    loader_map = _get_loaders(user, breakdown, constraints, level)

    generate_dimensions = _get_generate_dimensions(breakdown)
    for dimension in generate_dimensions:
        if dimension in constants.StructureDimension._ALL:
            loader = loader_map[dimension]
            dimension_rows = augmenter.make_dash_rows(dimension, loader.objs_ids, None)
            if dimension in HIERARCHICAL_DIMENSIONS:
                augmenter_fn = augmenter.get_report_augmenter_for_dimension(dimension, level)
                augmenter_fn(dimension_rows, loader)
            rows = _extend_rows(rows, dimension_rows)
        elif dimension in constants.TimeDimension._ALL:
            rows = _extend_rows(rows, [{dimension: date} for date in _get_representative_dates(dimension, constraints)])
        else:
            raise Exception("Invalid dimension for report: " + dimension)

    for dimension in breakdown:
        loader = loader_map[dimension]
        if loader is None:
            continue

        augmenter_fn = augmenter.get_report_augmenter_for_dimension(dimension, level)
        augmenter_fn(rows, loader)

    return rows


def _get_loaders(user, breakdown, constraints, level):
    loader_map = {}
    for dimension in breakdown:
        loader_cls = loaders.get_loader_for_dimension(dimension, level)
        if loader_cls is not None:
            loader_map[dimension] = loader_cls.from_constraints(user, constraints)
        else:
            loader_map[dimension] = None
    return loader_map


def _get_generate_dimensions(breakdown):
    # only take most specific dimension from hierarchical dimensions
    # returned dimensions are independent and need generated rows
    hierarchical = [dimension for dimension in HIERARCHICAL_DIMENSIONS if dimension in breakdown]
    non_hierarchical = [dimension for dimension in breakdown if dimension not in HIERARCHICAL_DIMENSIONS]
    return hierarchical[-1:] + non_hierarchical


def _extend_rows(rows, dimension_rows):
    new_rows = []
    for row in rows:
        for dimension_row in dimension_rows:
            new_row = copy.copy(row)
            new_row.update(dimension_row)
            new_rows.append(new_row)
    return new_rows
