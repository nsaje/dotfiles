import backtosql

from redshiftapi import models


def get_master_model_cls(use_publishers_view):
    return models.MVMasterPublishers() if use_publishers_view else models.MVMaster()


def get_master_conversions_model_cls(use_publishers_view):
    return models.MVConversionsPublishers() if use_publishers_view else models.MVConversions()


def get_master_touchpoints_model_cls(use_publishers_view):
    return models.MVTouchpointConversionsPublishers() if use_publishers_view else models.MVTouchpointConversions()


def get_joint_master_model_cls(use_publishers_view):
    return models.MVJointMasterPublishers() if use_publishers_view else models.MVJointMaster()


def prepare_query_all_base(breakdown, constraints, parents, use_publishers_view):
    model = get_master_model_cls(use_publishers_view)
    context = model.get_query_all_context(
        breakdown, constraints, parents,
        ['-clicks'] + breakdown,
        use_publishers_view)
    return _prepare_query_all_for_model(model, context)


def prepare_query_all_yesterday(breakdown, constraints, parents, use_publishers_view):
    model = get_master_model_cls(use_publishers_view)
    context = model.get_query_all_yesterday_context(
        breakdown, constraints, parents,
        ['-yesterday_cost'] + breakdown,
        use_publishers_view)
    return _prepare_query_all_for_model(model, context)


def prepare_query_all_conversions(breakdown, constraints, parents, use_publishers_view):
    model = get_master_conversions_model_cls(use_publishers_view)
    context = model.get_query_all_context(
        breakdown, constraints, parents,
        ['-count'] + breakdown,
        use_publishers_view)
    return _prepare_query_all_for_model(model, context)


def prepare_query_all_touchpoints(breakdown, constraints, parents, use_publishers_view):
    model = get_master_touchpoints_model_cls(use_publishers_view)
    context = model.get_query_all_context(
        breakdown, constraints, parents,
        ['-count'] + breakdown,
        use_publishers_view)
    return _prepare_query_all_for_model(model, context)


def _prepare_query_all_for_model(model, context, template_name='breakdown.sql'):
    sql = backtosql.generate_sql(template_name, context)
    return sql, context['constraints'].get_params()


def prepare_query_joint_base(breakdown, constraints, parents, orders, offset, limit, goals, use_publishers_view, skip_performance_columns=False):
    model = get_joint_master_model_cls(use_publishers_view)
    context = model.get_query_joint_context(breakdown, constraints, parents, orders, offset, limit, goals, use_publishers_view, skip_performance_columns)
    return _prepare_query_joint_for_model(context, 'breakdown_joint_base.sql')


def prepare_query_joint_levels(breakdown, constraints, parents, orders, offset, limit, goals, use_publishers_view):
    model = get_joint_master_model_cls(use_publishers_view)
    context = model.get_query_joint_context(breakdown, constraints, parents, orders, offset, limit, goals, use_publishers_view)
    return _prepare_query_joint_for_model(context, 'breakdown_joint_levels.sql')


def _prepare_query_joint_for_model(context, template_name):
    sql = backtosql.generate_sql(template_name, context)

    params = []
    if 'conversions_constraints' in context and context['conversions_constraints'].was_generated():
        params.extend(context['conversions_constraints'].get_params())

    if 'touchpoints_constraints' in context and context['touchpoints_constraints'].was_generated():
        params.extend(context['touchpoints_constraints'].get_params())

    params.extend(context['yesterday_constraints'].get_params())
    params.extend(context['constraints'].get_params())

    return sql, params


def prepare_query_structure_with_stats(breakdown, constraints, use_publishers_view):
    model = get_master_model_cls(use_publishers_view)
    context = model.get_query_all_context(
        breakdown, constraints, None, ['-media_cost'] + breakdown,
        use_publishers_view)
    return _prepare_query_all_for_model(model, context, 'breakdown_no_aggregates.sql')
