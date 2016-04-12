from django.template import loader
from backtosql import helpers


class BackToSQLException(Exception):
    pass


def generate_sql(template_name, context):
    template = loader.get_template(template_name)
    return helpers.clean_sql(template.render(context))


class TemplateColumn(object):
    def __init__(self, template_name, context=None, alias=None, group=None):
        self.template_name = template_name
        self.context = context

        self.group = group
        self.alias = alias  # can be set later through model, TODO rename output_name

    def _get_default_context(self, prefix):
        return {
            'p': helpers.clean_prefix(prefix),
            'alias': helpers.clean_alias(self.alias),
        }

    def g(self, prefix=None):
        context = self._get_default_context(prefix)
        context['alias'] = helpers.clean_alias(None)
        if self.context:
            context.update(self.context)

        return generate_sql(self.template_name, context)

    def g_alias(self, prefix=None):
        alias = helpers.clean_alias(self.alias)
        if not alias:
            raise BackToSQLException("Alias is not defined")
        return "{}{}".format(helpers.clean_prefix(prefix), alias)

    def g_w_alias(self, prefix=None):
        context = self._get_default_context(prefix)
        if self.context:
            context.update(self.context)

        return generate_sql(self.template_name, context)


class Column(TemplateColumn):
    def __init__(self, column_name, alias=None, group=None):
        super(Column, self).__init__('column.sql', {'column_name': column_name}, alias=alias, group=group)


class OutputColumnWrapper(TemplateColumn):
    def __init__(self, column, template_name, context):
        self.column = column
        super(OutputColumnWrapper, self).__init__(template_name, context, alias=None, group=None)

    def _get_default_context(self, prefix):
        return {
            'p': helpers.clean_prefix(prefix),
            'alias': helpers.clean_alias(self.column.alias),
            'column': self.column,
        }


class OrderWrapper(OutputColumnWrapper):
    def __init__(self, column, direction_hint):
        super(OrderWrapper, self).__init__(column, 'order.sql', {'direction': helpers.get_order(direction_hint)})


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
    """
    # Use builtin https://docs.djangoproject.com/en/1.9/topics/db/sql/#executing-custom-sql-directly
    translation to map python-sql fields
    # TODO: we need to register outer fields that they need to be converted
    """

    __COLUMNS__ = None  # columns list
    __COLUMNS_DICT__ = None  # columns dict (alias - column object)

    @classmethod
    def _init_columns(cls):
        if cls.__COLUMNS__:
            # already initialized
            return

        columns = [(name, getattr(cls, name)) for name in dir(cls)
                   if isinstance(getattr(cls, name), TemplateColumn)]
        for name, col in columns:
            if col.alias is None:
                col.alias = name

        cls.__COLUMNS__ = [x[1] for x in columns]
        cls.__COLUMNS_DICT__ = dict(columns)

    @classmethod
    def get_columns(cls):
        return cls.__COLUMNS__

    @classmethod
    def get_column(cls, alias):
        return cls.__COLUMNS_DICT__[helpers.clean_alias(alias)]

    @classmethod
    def select_columns(cls, subset=None, group=None):
        columns = cls.get_columns()
        if group:
            columns = [x for x in columns if x.group == group]

        if subset:
            columns_dict = {x.alias: x for x in columns}
            columns = []

            for alias in subset:
                alias = helpers.clean_alias(alias)
                if alias in columns_dict:
                    columns.append(columns_dict[alias])

        return columns
