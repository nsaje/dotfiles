import copy

from dash.dashapi import augmenter
from dash.dashapi import augmenter_reports
from dash.dashapi import loaders

from stats import constants
from redshiftapi.postprocess import _get_representative_dates


def annotate(rows, user, breakdown, constraints, goals):
    for dimension in breakdown:
        loader_cls = loaders.get_loader_for_dimension(dimension, None)  # level should not be needed
        if loader_cls is None:
            continue

        loader = loader_cls.from_constraints(user, constraints)
        augmenter_fn = augmenter_reports.get_augmenter_for_dimension(dimension)
        augmenter_fn(rows, loader)


def query(user, breakdown, constraints, goals):
    # TODO: this probably does not work when two dimensions in breakdown are loaded from db
    rows = None
    for dimension in breakdown:
        loader_cls = loaders.get_loader_for_dimension(dimension, None)
        if loader_cls is not None:
            loader = loader_cls.from_constraints(user, constraints)
            dimension_rows = augmenter.make_dash_rows(dimension, loader.objs_ids, None)

            augmenter_fn = augmenter_reports.get_augmenter_for_dimension(dimension)
            augmenter_fn(dimension_rows, loader)
        elif dimension in constants.TimeDimension._ALL:
            dimension_rows = [{
                dimension: date
            } for date in _get_representative_dates(dimension, constraints)]
        else:
            raise Exception('Invalid dimension for report.')

        if rows is None:
            rows = dimension_rows
        else:
            new_rows = []
            for row in rows:
                for dimension_row in dimension_rows:
                    new_row = copy.copy(row)
                    new_row.update(dimension_row)
                    new_rows.append(new_row)
            rows = new_rows

    return rows
