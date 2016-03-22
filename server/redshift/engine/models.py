from django.template import loader
"""
Default API

m = RSModel(**kwargs)

query = prepare_query('template.sql', constraints)
m.execute(query)

"""


# rename: breakdown query, and won't be a part of engine
class RSQuery(object):
    """
    Should be immutable.
    """

    def __init__(self, template_name):
        self.template_name = template_name

    def generate(self, context):
        template = loader.get_template(self.template_name)
        return template.render(context)

    def _generate_constraints(self, constraints):
        # TODO: use existing RSQ?
        # We should probably stick to simple constraints.

        # we need prefixes, so we need model, so we complicate,
        # what if we just pass the fields to template and let template deal with it?
        pass


class RSBreakdownQuery(RSQuery):
    def generate(self, breakdown_columns_list, aggregate_columns_dict,
                 constraints_dict, order_columns_list, page, view):
        # TODO: This is kinda out of this library, this is a helper for breakdowns
        template = loader.get_template(self.template_name)
        return template.render({
            'breakdowns': breakdown_columns_list,
            'aggregates': aggregate_columns_dict,
            'order': order_columns_list,
            'page': page,
            'view': view,
        })


class RSModel(object):
    """
    Should be immutable.

    # Use builtin https://docs.djangoproject.com/en/1.9/topics/db/sql/#executing-custom-sql-directly
    translation to map python-sql fields
    """

    def __init__(self):
        self.columns = self._init_columns()

    def _init_columns(self):
        # this is not the nicest api
        cols = [(name, getattr(self, name))
                for name in dir(self)
                if isinstance(
                    getattr(self, name), RSColumn)]

        for name, col in cols:
            col.pyname = name

        return cols

    def _select_columns(self, columns, subset=None):
        # it is important that the order of fields is preserved
        # so that we don't:
        #     - recompile queries
        #     - mess up the breakdown
        # this behaviour needs to have tests

        if subset is not None:
            columns_dict = dict(columns)

            columns = []
            for x in subset:
                columns.append((x, columns_dict[x]))
        return [x[1] for x in columns]

    # move this to separate breakdown model
    def get_breakdown_columns(self, subset=None):
        return self._select_columns(
            [
                (n, c)
                for n, c in self.columns
                if c.column_type == RSColumnType.BREAKDOWN
            ], subset)

    def get_aggregate_columns(self, subset=None):
        return self._select_columns(
            [
                (n, c)
                for n, c in self.columns
                if c.column_type == RSColumnType.AGGREGATE
            ], subset)


class RSColumnType:
    BREAKDOWN = 1
    AGGREGATE = 2


class RSColumn(object):
    """
    Should be immutable.
    """

    def __init__(self,
                 column_name,
                 convert_to_py=None,
                 column_type=RSColumnType.BREAKDOWN,
                 **kwargs):
        self.column_name = column_name
        self.convert_to_py = convert_to_py
        self.column_type = column_type
        self.pyname = None  # set later through model

    def _format_prefix(self, prefix=None):
        if prefix and not prefix.endswith('.'):
            prefix = prefix + '.'
        return prefix or ""

    def pfx(self, prefix=None):
        col = "{}{}".format(self._format_prefix(prefix), self.column_name)
        return col if col == self.column_name else "{} {}".format(
            col, self.column_name)


class RSTemplateColumn(RSColumn):
    def __init__(self, template_name, column_name, **kwargs):
        self.template_name = template_name
        self.context = kwargs
        super(RSTemplateColumn, self).__init__(column_name, **kwargs)

    def pfx(self, prefix=None):
        template = loader.get_template(self.template_name)
        context = {'p': self._format_prefix(prefix), 'alias': self.column_name}
        context.update(self.context)

        return template.render(context)
