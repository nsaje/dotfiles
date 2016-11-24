from dash.dashapi import augmenter
from dash.dashapi import loaders


def annotate(rows, user, breakdown, constraints, goals, order):
    for dimension in breakdown:
        loader_cls = loaders.get_loader_for_dimension(dimension, None)  # level should not be needed
        if loader_cls is None:
            continue

        loader = loader_cls.from_constraints(user, constraints)
        augmenter_fn = augmenter.get_report_augmenter_for_dimension(dimension)
        augmenter_fn(rows, loader)
