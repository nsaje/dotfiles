from backtosql import helpers


class Q(object):
    '''
    Used for constructing the WHERE filter of the query that supports AND, OR and NOT,
    similar to django Q (https://github.com/django/django/blob/master/django/db/models/query_utils.py)
    '''

    AND = ' AND '
    OR = ' OR '

    def __init__(self, model, *args, **kwargs):
        self.negate = False
        self.join_operator = self.AND
        self.children = list(args) + sorted(list(kwargs.iteritems()))
        self.model = model

        # cache, used to preserve the order of params
        # TODO can't get them out afterwards in the same order
        # currently only supported for 1 prefix/query
        self.params = None
        self.query = None
        self.prefix = None

    def _combine(self, other, join_operator):
        parent = type(self)(self.model, *[self, other])
        parent.join_operator = join_operator
        return parent

    def __and__(self, other):
        return self._combine(other, self.AND)

    def __or__(self, other):
        return self._combine(other, self.OR)

    def __invert__(self):
        self.negate = not self.negate
        return self

    def g(self, prefix=None):
        if self.prefix is not None and self.prefix is not prefix:
            raise Exception("Only 1 prefix per Q")

        self.query, self.params = self._g(prefix)

        self.prefix = prefix

        return self.query

    def get_params(self):
        # TODO wont work if taken different order
        _, params = self._g()
        return params

    def _g(self, prefix=None):
        # BUG: This code will overflow the stack in case there are too many WHERE conditions
        parts = []
        params = []

        for child in self.children:
            if isinstance(child, type(self)):
                child_parts, child_params = child._g(prefix)
            else:
                child_parts, child_params = self._generate_sql(child, prefix)

            parts.append(child_parts)
            params.extend(child_params)

        if not parts and not params:
            return '', []

        ret = '(' + self.join_operator.join(parts) + ')'
        if self.negate:
            ret = 'NOT ' + ret

        return ret, params

    def _prepare_constraint(self, constraint):
        constraint_name, value = constraint

        parts = constraint_name.split("__")
        alias = helpers.clean_alias(parts[0])
        column = self.model.get_column(alias)

        # TODO this needs to be solved differently
        if not column or not column.column_name:
            raise Exception("TODO write exception, not supported column")

        if len(parts) == 2:
            operator = parts[1]
        else:
            operator = "eq"

        return column, operator, value

    def _generate_sql(self, constraint, prefix):
        column, operator, value = self._prepare_constraint(constraint)
        if operator == "lte":
            return '{}<=%s'.format(column.g(prefix)), [value]
        elif operator == "lt":
            return '{}<%s'.format(column.g(prefix)), [value]
        elif operator == "gte":
            return '{}>=%s'.format(column.g(prefix)), [value]
        elif operator == "gt":
            return '{}>%s'.format(column.g(prefix)), [value]
        elif operator == "eq":
            if helpers.is_collection(value):
                if value:
                    return '{} IN %s'.format(column.g(prefix)), [value]
                else:
                    return 'FALSE', []
            else:
                return '{}=%s'.format(column.g(prefix)), [value]
        elif operator == "neq":
            if helpers.is_collection(value):
                if value:
                    return '{} NOT IN ({})'.format(column.g(prefix), ','.join(["%s"] * len(value))), value
                else:
                    return 'TRUE', []
            else:
                return '{}!=%s'.format(column.g(prefix)), [value]
        else:
            raise Exception("Unknown constraint type: {}".format(operator))
