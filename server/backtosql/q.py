from backtosql import helpers


class Q(object):
    '''
    Used for constructing the WHERE filter of the query that supports AND, OR and NOT,
    similar to django Q (https://github.com/django/django/blob/master/django/db/models/query_utils.py)
    '''

    AND = ' AND '
    OR = ' OR '

    def __init__(self, *args, **kwargs):
        self.negate = False
        self.join_operator = self.AND
        self.children = list(args) + list(kwargs.iteritems())

    def _combine(self, other, join_operator):
        parent = type(self)(*[self, other])
        parent.join_operator = join_operator
        return parent

    def __and__(self, other):
        return self._combine(other, self.AND)

    def __or__(self, other):
        return self._combine(other, self.OR)

    def __invert__(self):
        self.negate = not self.negate
        return self

    def expand(self, model, prefix=None):
        # BUG: This code will overflow the stack in case there are too many WHERE conditions
        parts = []
        params = []

        for child in self.children:
            if isinstance(child, type(self)):
                child_parts, child_params = child.expand(prefix, model)
            else:
                child_parts, child_params = self._generate_sql(child, prefix, model)

            parts.append(child_parts)
            params.extend(child_params)

        if not parts and not params:
            return '', []

        ret = '(' + self.join_operator.join(parts) + ')'
        if self.negate:
            ret = 'NOT ' + ret

        return ret, params

    def _prepare_constraint(self, constraint, model):
        constraint_name, value = constraint

        parts = constraint_name.split("__")
        alias = helpers.clean_alias(parts[0])
        column = model.get_column(alias)

        # TODO this needs to be solved differently
        if not column or not column.column_name:
            raise Exception("TODO write exception, not supported column")

        if len(parts) == 2:
            operator = parts[1]
        else:
            operator = "eq"

        return column, operator, value

    def _generate_sql(self, constraint, prefix, model):
        column, operator, value = self._prepare_constraint(constraint, model)
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
