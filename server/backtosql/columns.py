from . import helpers


class TemplateColumn(object):
    def __init__(self, template_name, context=None, group=None, alias=None):
        self.template_name = template_name
        self.context = context or {}

        self.group = group
        self.alias = alias  # is set automatically through model if defined on a model

    @property
    def column_name(self):
        return self.context.get("column_name")

    def _get_default_context(self, prefix):
        return {"p": helpers.clean_prefix(prefix), "alias": ""}

    def _get_alias(self):
        alias = helpers.clean_alias(self.alias)
        if not alias:
            raise helpers.BackToSQLException("Alias is not defined")
        return alias

    def only_column(self, prefix=None):
        context = self._get_default_context(prefix)

        if self.context:
            context.update(self.context)

        return helpers.generate_sql(self.template_name, context)

    def only_alias(self, prefix=None):
        return "{}{}".format(helpers.clean_prefix(prefix), self._get_alias())

    def column_as_alias(self, prefix=None):
        context = self._get_default_context(prefix)
        context["alias"] = self._get_alias()

        if self.context:
            context.update(self.context)

        return helpers.generate_sql(self.template_name, context)

    def column_equal(self, table1, table2):
        return "{} = {}".format(self.only_alias(table1), self.only_alias(table2))

    def as_order(self, direction_hint, nulls=None):
        return OrderColumn(self, direction_hint, nulls)


class Column(TemplateColumn):
    ZERO_VALUE_PLACEHOLDERS = {str: "'~N/A~'", int: -1}

    def __init__(self, column_name, group=None, alias=None, null_type=None):
        super(Column, self).__init__("column.sql", {"column_name": column_name}, alias=alias, group=group)
        self.null_type = null_type

    def column_as_alias_coalesce_zero_value(self, prefix=None):
        zero_value = self.ZERO_VALUE_PLACEHOLDERS.get(self.null_type)
        if zero_value is None:
            return self.column_as_alias(prefix)
        column_name = self.context.get("column_name")
        prefix = helpers.clean_prefix(prefix)
        return f"COALESCE({prefix}{column_name}, {zero_value}) AS {self._get_alias()}"

    def only_alias_nullif_zero_value(self, prefix=None):
        column_name = self.only_alias(prefix)
        zero_value = self.ZERO_VALUE_PLACEHOLDERS.get(self.null_type)
        if zero_value is None:
            return column_name
        return f"NULLIF({column_name}, {zero_value}) AS {self._get_alias()}"


class OrderColumn(TemplateColumn):
    def __init__(self, column, direction_hint, nulls=None):
        self.column = column
        self.nulls = nulls

        super(OrderColumn, self).__init__(
            "order.sql", self.order_context(direction_hint), group=self.column.group, alias=self.column.alias
        )

    def order_context(self, direction_hint):
        return {"direction": helpers.get_order(direction_hint, self.nulls)}

    def only_column(self, prefix=None):
        context = {"column_render": self.column.only_column(prefix)}

        if self.context:
            context.update(self.context)

        return helpers.generate_sql(self.template_name, context)

    def only_alias(self, prefix=None):
        context = {"column_render": self.column.only_alias(prefix)}

        if self.context:
            context.update(self.context)

        return helpers.generate_sql(self.template_name, context)

    def column_as_alias(self, prefix=None):
        raise helpers.BackToSQLException('SQL syntax error, "column AS alias" does not make sense for order')

    def as_order(self, *args, **kwargs):
        raise helpers.BackToSQLException("Already OrderColumn")
