import helpers


class TemplateColumn(object):

    def __init__(self, template_name, context=None, group=None, alias=None):
        self.template_name = template_name
        self.context = context or {}

        self.group = group
        self.alias = alias  # is set automatically through model if defined on a model

    @property
    def column_name(self):
        return self.context.get('column_name')

    def _get_default_context(self, prefix):
        return {
            'p': helpers.clean_prefix(prefix),
            'alias': '',
        }

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
        context['alias'] = self._get_alias()

        if self.context:
            context.update(self.context)

        return helpers.generate_sql(self.template_name, context)

    def column_equal_or_null(self, table1, table2):
        context = {
            'first_table_column': self.only_column(table1),
            'second_table_column': self.only_column(table2),
        }
        return helpers.generate_sql('column_equal_or_null.sql', context)

    def as_order(self, direction_hint, nulls=None):
        return OrderColumn(self, direction_hint, nulls)


class Column(TemplateColumn):

    def __init__(self, column_name, group=None, alias=None):
        super(Column, self).__init__('column.sql', {'column_name': column_name}, alias=alias, group=group)


class OrderColumn(TemplateColumn):
    def __init__(self, column, direction_hint, nulls=None):
        self.column = column
        self.nulls = nulls

        super(OrderColumn, self).__init__(
            'order.sql',
            self.order_context(direction_hint),
            group=self.column.group,
            alias=self.column.alias)

    def order_context(self, direction_hint):
        return {
            'direction': helpers.get_order(direction_hint, self.nulls)
        }

    def only_column(self, prefix=None):
        context = {
            'column_render': self.column.only_column(prefix),
        }

        if self.context:
            context.update(self.context)

        return helpers.generate_sql(self.template_name, context)

    def only_alias(self, prefix=None):
        context = {
            'column_render': self.column.only_alias(prefix),
        }

        if self.context:
            context.update(self.context)

        return helpers.generate_sql(self.template_name, context)

    def column_as_alias(self, prefix=None):
        raise helpers.BackToSQLException('SQL syntax error, "column AS alias" does not make sense for order')

    def as_order(self, *args, **kwargs):
        raise helpers.BackToSQLException('Already OrderColumn')
