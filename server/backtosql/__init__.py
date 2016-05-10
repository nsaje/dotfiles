from functools import partial

from django.template import loader
from backtosql import helpers
from backtosql.q import Q


class BackToSQLException(Exception):
    pass


def generate_sql(template_name, context):
    template = loader.get_template(template_name)
    return helpers.clean_sql(template.render(context))


class TemplateColumn(object):

    def __init__(self, template_name, context={}, group=None, alias=None):
        if not context:
            context = {}

        self.template_name = template_name
        self.context = context

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
            raise BackToSQLException("Alias is not defined")
        return alias

    def g(self, prefix=None):
        context = self._get_default_context(prefix)

        if self.context:
            context.update(self.context)

        return generate_sql(self.template_name, context)

    def g_alias(self, prefix=None):
        return "{}{}".format(helpers.clean_prefix(prefix), self._get_alias())

    def g_w_alias(self, prefix=None):
        context = self._get_default_context(prefix)
        context['alias'] = self._get_alias()
        if self.context:
            context.update(self.context)

        return generate_sql(self.template_name, context)

    def as_order(self, direction_hint):
        return OrderColumn(self, direction_hint)


class Column(TemplateColumn):

    def __init__(self, column_name, group=None, alias=None):
        super(Column, self).__init__('column.sql', {'column_name': column_name}, alias=alias, group=group)


class OrderColumn(TemplateColumn):
    def __init__(self, column, direction_hint):
        self.column = column

        super(OrderColumn, self).__init__(
            'order.sql',
            self.order_context(direction_hint),
            group=self.column.group,
            alias=self.column.alias)

    def order_context(self, direction_hint):
        return {
            'direction': helpers.get_order(direction_hint)
        }

    def g(self, prefix=None):
        context = {
            'column_render': self.column.g(prefix),
        }

        if self.context:
            context.update(self.context)

        return generate_sql(self.template_name, context)

    def g_alias(self, prefix=None):
        context = {
            'column_render': self.column.g_alias(prefix),
        }

        if self.context:
            context.update(self.context)

        return generate_sql(self.template_name, context)

    def g_w_alias(self, prefix=None):
        raise BackToSQLException('SQL syntax error')

    def as_order(self, *args, **kwargs):
        raise BackToSQLException('Already OrderColumn')


class ModelMeta(type):
    """
    ModelMeta is a meta class of Model. It takes care for class columns initialization.
    """
    def __new__(cls, name, parents, dct):
        model_class = super(ModelMeta, cls).__new__(cls, name, parents, dct)
        model_class._init_columns()
        return model_class


class Model(object):
    __metaclass__ = ModelMeta

    __COLUMNS__ = None
    __COLUMNS_DICT__ = None

    @classmethod
    def _init_columns(cls):
        columns = [(name, getattr(cls, name)) for name in dir(cls)
                   if isinstance(getattr(cls, name), TemplateColumn)]

        for name, col in columns:
            if col.alias is None:
                col.alias = name

        cls.__COLUMNS__ = [x[1] for x in columns]
        cls.__COLUMNS_DICT__ = dict(columns)

    @classmethod
    def get_columns(cls):
        return cls.__COLUMNS__[:]

    @classmethod
    def get_column(cls, alias):
        return cls.__COLUMNS_DICT__[helpers.clean_alias(alias)]

    @classmethod
    def select_columns(cls, subset=None, group=None):
        if subset:
            columns = []
            unknown = []

            for alias in subset:
                alias = helpers.clean_alias(alias)
                if alias in cls.__COLUMNS_DICT__:
                    columns.append(cls.__COLUMNS_DICT__[alias])
                else:
                    unknown.append(alias)

            # TODO add test
            if unknown:
                raise BackToSQLException('Unknown columns in subset {}'.format(unknown))

        else:
            columns = cls.get_columns()

        if group:
            columns = [x for x in columns if x.group == group]

        return columns

    @classmethod
    def get_constraints(cls, constraints_dict):
        return Q(cls, **constraints_dict)

    @classmethod
    def select_order(cls, subset):
        return [cls.get_column(c).as_order(c) for c in subset]