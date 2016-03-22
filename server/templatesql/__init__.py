class RSQuery(object):
    def __init__(self, template_name):
        self.template_name = template_name

    def generate(self, context):
        template = loader.get_template(self.template_name)
        return template.render(context)


class RSModel(object):
    """
    # Use builtin https://docs.djangoproject.com/en/1.9/topics/db/sql/#executing-custom-sql-directly
    translation to map python-sql fields
    """

    __COLUMNS__ = None

    @classmethod
    def get_columns(cls):
        if cls.__COLUMNS__ is None:
            cols = [(name, getattr(cls, name))
                    for name in dir(cls)
                    if isinstance(
                        getattr(cls, name), RSColumn)]

            for name, col in cols:
                col.pyname = name

            # cache them
            cls.__COLUMNS__ = cols

        return cls.__COLUMNS__

    @classmethod
    def select_columns(cls, subset=None, group=None):
        # it is important that the order of fields is preserved
        # so that we don't:
        #     - recompile queries
        #     - mess up the breakdown
        # this behaviour needs to have tests
        columns = cls.get_columns()
        if group:
            columns = [x for x in cls.get_columns() if x[1].group == group]

        if subset is not None:
            columns_dict = dict(columns)

            columns = []
            for x in subset:
                columns.append((x, columns_dict[x]))

        # return only column objects
        return [x[1] for x in columns]


class RSColumn(object):
    def __init__(self, column_name, group=None):
        self.column_name = column_name
        self.group = group
        self.pyname = None  # set later through model

    @classmethod
    def _format_prefix(cls, prefix=None):
        if prefix and not prefix.endswith('.'):
            prefix = prefix + '.'
        return prefix or ""

    def gen(self, prefix=None):
        col = "{}{}".format(self._format_prefix(prefix), self.column_name)
        return col if col == self.pyname else "{} {}".format(col, self.pyname)


class RSTemplateColumn(RSColumn):
    def __init__(self, template_name, column_name, group, context=None):
        self.template_name = template_name
        self.context = context
        super(RSTemplateColumn, self).__init__(column_name, group)

    def gen(self, prefix=None):
        template = loader.get_template(self.template_name)
        context = {'p': self._format_prefix(prefix),
                   'column_name': self.column_name,
                   'alias': self.pyname}
        context.update(self.context)

        return template.render(context)
