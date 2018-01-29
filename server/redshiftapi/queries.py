import backtosql

import exceptions
import models
import view_selector
import helpers


def prepare_query_all_base(breakdown, constraints, parents, use_publishers_view):
    needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents)
    view = view_selector.get_best_view_base(needed_dimensions, use_publishers_view)
    model = models.MVMaster()

    context = model.get_query_all_context(
        breakdown, constraints, parents,
        ['-clicks'] + breakdown,
        view)

    return _prepare_query_all_for_model(model, context)


def prepare_query_all_yesterday(breakdown, constraints, parents, use_publishers_view):
    needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents)
    view = view_selector.get_best_view_base(needed_dimensions, use_publishers_view)

    model = models.MVMaster()

    context = model.get_query_all_yesterday_context(
        breakdown, constraints, parents,
        ['-yesterday_cost'] + breakdown, view)

    return _prepare_query_all_for_model(model, context)


def prepare_query_all_conversions(breakdown, constraints, parents):
    needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents)
    view = view_selector.get_best_view_conversions(needed_dimensions)

    if not view:
        raise exceptions.ViewNotAvailable()

    model = models.MVConversions()

    context = model.get_query_all_context(
        breakdown, constraints, parents,
        ['-count'] + breakdown,
        view)

    return _prepare_query_all_for_model(model, context)


def prepare_query_all_touchpoints(breakdown, constraints, parents):
    needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents)
    view = view_selector.get_best_view_touchpoints(needed_dimensions)

    if not view:
        raise exceptions.ViewNotAvailable()

    model = models.MVTouchpointConversions()

    context = model.get_query_all_context(
        breakdown, constraints, parents,
        ['-count'] + breakdown,
        view)

    return _prepare_query_all_for_model(model, context)


def _prepare_query_all_for_model(model, context, template_name='breakdown.sql'):
    context['constraints'].use_tmp_tables = True
    sql = backtosql.generate_sql(template_name, context)
    return sql, context['constraints'].get_params(), context['constraints'].get_create_tmp_tables(), context['constraints'].get_drop_tmp_tables()


def prepare_query_joint_base(breakdown, constraints, parents, orders, offset, limit, goals, use_publishers_view, skip_performance_columns=False):
    needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents)
    views = {
        'base': view_selector.get_best_view_base(needed_dimensions, use_publishers_view),
        'yesterday': view_selector.get_best_view_base(needed_dimensions, use_publishers_view),
        'conversions': view_selector.get_best_view_conversions(needed_dimensions),
        'touchpoints': view_selector.get_best_view_touchpoints(needed_dimensions),
    }

    context = models.MVJointMaster().get_query_joint_context(
        breakdown, constraints, parents, orders, offset, limit,
        goals, views,
        skip_performance_columns,
        supports_conversions=view_selector.supports_conversions(views['base'], views['conversions']),
        supports_touchpoints=view_selector.supports_conversions(views['base'], views['touchpoints']))

    return _prepare_query_joint_for_model(context, 'breakdown_joint_base.sql')


def prepare_query_joint_levels(breakdown, constraints, parents, orders, offset, limit, goals, use_publishers_view):
    needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents)
    views = {
        'base': view_selector.get_best_view_base(needed_dimensions, use_publishers_view),
        'yesterday': view_selector.get_best_view_base(needed_dimensions, use_publishers_view),
        'conversions': view_selector.get_best_view_conversions(needed_dimensions),
        'touchpoints': view_selector.get_best_view_touchpoints(needed_dimensions),
    }

    context = models.MVJointMaster().get_query_joint_context(
        breakdown, constraints, parents, orders, offset, limit, goals, views,
        supports_conversions=view_selector.supports_conversions(views['base'], views['conversions']),
        supports_touchpoints=view_selector.supports_conversions(views['base'], views['touchpoints']))

    return _prepare_query_joint_for_model(context, 'breakdown_joint_levels.sql')


def _prepare_query_joint_for_model(context, template_name):
    constraints_list = ['conversions_constraints', 'touchpoints_constraints', 'yesterday_constraints', 'constraints']
    constraints_list = [c for c in constraints_list if c in context]
    for constraints in constraints_list:
        context[constraints].use_tmp_tables = True

    sql = backtosql.generate_sql(template_name, context)

    all_params = []
    all_create_tmp_tables = None
    all_drop_tmp_tables = None

    for constraints in constraints_list:
        if not context[constraints].was_generated():
            continue
        all_params.extend(context[constraints].get_params())
        create_tmp_tables = context[constraints].get_create_tmp_tables()
        drop_tmp_tables = context[constraints].get_drop_tmp_tables()
        if create_tmp_tables is not None:
            if all_create_tmp_tables is None:
                all_create_tmp_tables = create_tmp_tables
            else:
                all_create_tmp_tables = (
                    all_create_tmp_tables[0] + create_tmp_tables[0],
                    all_create_tmp_tables[1] + create_tmp_tables[1],
                )
        if drop_tmp_tables is not None:
            if all_drop_tmp_tables is None:
                all_drop_tmp_tables = drop_tmp_tables
            else:
                all_drop_tmp_tables = (
                    all_drop_tmp_tables[0] + drop_tmp_tables[0],
                    all_drop_tmp_tables[1] + drop_tmp_tables[1],
                )

    return sql, all_params, all_create_tmp_tables, all_drop_tmp_tables


def prepare_query_structure_with_stats(breakdown, constraints, use_publishers_view):
    needed_dimensions = helpers.get_all_dimensions(breakdown, constraints, parents=None)
    view = view_selector.get_best_view_base(needed_dimensions, use_publishers_view)

    model = models.MVMaster()

    context = model.get_query_all_context(
        breakdown, constraints, None, ['-media_cost'] + breakdown,
        view)

    return _prepare_query_all_for_model(model, context, 'breakdown_no_aggregates.sql')
