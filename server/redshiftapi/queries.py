import backtosql


def prepare_generic_lvl1(model, breakdown, constraints, breakdown_constraints,
                         order, page, page_size):

    context = _get_default_context(model, breakdown, constraints, breakdown_constraints, order, page, page_size)

    sql = backtosql.generate_sql('breakdown_lvl1.sql', context)

    params = context['constraints'].get_params()

    return sql, params


def prepare_generic_lvl2(model, breakdown, constraints, breakdown_constraints,
                         order, page, page_size):
    context = _get_default_context(model, breakdown, constraints, breakdown_constraints, order, page, page_size)

    sql = backtosql.generate_sql('breakdown_lvl2.sql', context)

    # this is template specific - based on what comes first
    params = context['breakdown_constraints'].get_params()
    params.extend(context['constraints'].get_params())

    return sql, params


def prepare_generic_lvl3(model, breakdown, constraints, breakdown_constraints,
                         order, page, page_size):
    # the last one is always time
    pass


def _get_default_context(model, breakdown, constraints, breakdown_constraints,
                         order, page, page_size):
    """
    Returns the template context that is used by most of templates
    """

    constraints = backtosql.Q(model, **constraints)
    breakdown_constraints = _prepare_breakdown_constraints(breakdown_constraints)

    context = {
        'view': model.get_best_view(breakdown),
        'breakdown': model.get_breakdown(breakdown),
        'constraints': constraints,
        'breakdown_constraints': breakdown_constraints,
        'aggregates': model.get_aggregates(),
        'order': model.select_order(order),
        'offset': (page - 1) * page_size,
        'limit': page * page_size,
    }

    return context


def _prepare_breakdown_constraints(breakdown_constraints):
    """
    Create OR separated AND statements based on breakdown_constraints.
    Eg.:

    (a AND b) OR (c AND d)
    """
    if not breakdown_constraints:
        return None

    bq = backtosql.Q(model, **breakdown_constraints[0])

    for branch in breakdown_constraints[1:]:
        bq |= backtosql.Q(model, **branch)

    return bq