from backtosql import helpers
from backtosql import temp_tables


def dissect_constraint_key(constraint_key):
    return constraint_key.split("__")


class Q(object):
    """
    Used for constructing the WHERE filter of the query that supports AND, OR and NOT,
    similar to django Q (https://github.com/django/django/blob/master/django/db/models/query_utils.py)
    """

    AND = " AND "
    OR = " OR "
    MAX_RECURSION_DEPTH = 900

    def __init__(self, model, *args, **kwargs):
        self.negate = False
        self.join_operator = self.AND
        self.children = list(args) + sorted(list(kwargs.items()))
        self.model = model

        # cache, used to preserve the order of parameters
        self.params = None
        self.query = None
        self.prefix = None

    def __str__(self):
        children = ",".join(str(child) for child in self.children)
        return f"Q({children})"

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

    def was_generated(self):
        return self.params is not None

    def generate(self, prefix=None):
        if self.prefix is not None and self.prefix != prefix:
            raise helpers.BackToSQLException("Only 1 prefix per Q")

        self.query, self.params = self._generate(prefix)
        self.prefix = prefix

        return self.query

    @classmethod
    def none(cls, model):
        # similar as to how django queryset none() works
        return cls(model, __none=None)

    def get_params(self):
        if not self.was_generated():
            raise helpers.BackToSQLException("Query not yet generated")
        return self.params

    def _generate(self, prefix=None, depth=1):
        if depth >= self.MAX_RECURSION_DEPTH:
            # This code would overflow the stack in case there are too many
            # nested WHERE conditions. This is a limit defined by max recursion
            # limit on your system. Anyway if you reach this limit try to redesign
            # your logics so it won't generate a tree so deep.
            raise helpers.BackToSQLException("Q recursion too deep {}".format(self.MAX_RECURSION_DEPTH))

        parts = []
        params = []

        for child in self.children:
            if isinstance(child, type(self)):
                child_parts, child_params = child._generate(prefix, depth + 1)
            else:
                child_parts, child_params = self._generate_sql(child, prefix)

            parts.append(child_parts)
            params.extend(child_params)

        if not parts and not params:
            return "1=1", []

        ret = "(" + self.join_operator.join(parts) + ")"
        if self.negate:
            ret = "NOT " + ret

        return ret, params

    def _prepare_constraint(self, constraint):
        constraint_name, value = constraint

        parts = dissect_constraint_key(constraint_name)
        alias = helpers.clean_alias(parts[0])

        if len(parts) == 2:
            operator = parts[1]
        else:
            operator = "eq"

        if alias == "":
            return None, operator, value

        column = self.model.get_column(alias)
        return column, operator, value

    def _generate_sql(self, constraint, prefix):
        column, operator, value = self._prepare_constraint(constraint)

        operator_dict = {"lte": "{}<=%s", "lt": "{}<%s", "gte": "{}>=%s", "gt": "{}>%s"}

        if operator == "none":
            return "1=%s", [2]

        if operator in operator_dict:
            return operator_dict[operator].format(column.only_column(prefix)), [value]
        elif operator == "eq":
            if isinstance(value, temp_tables.ConstraintTempTable):
                return "{} IN (SELECT {} FROM {})".format(column.only_column(prefix), value.constraint, value.name), []
            if helpers.is_collection(value):
                if value:
                    return "{}=ANY(%s)".format(column.only_column(prefix)), [value]
                return "FALSE", []

            if value is None:
                return "{} IS %s".format(column.only_column(prefix)), [value]
            return "{}=%s".format(column.only_column(prefix)), [value]

        elif operator == "neq":
            if helpers.is_collection(value):
                if value:
                    return "{}!=ANY(%s)".format(column.only_column(prefix)), [value]

                return "TRUE", []

            if value is None:
                return "{} IS NOT %s".format(column.only_column(prefix)), [value]

            return "{}!=%s".format(column.only_column(prefix)), [value]

        raise helpers.BackToSQLException("Unknown constraint type: {}".format(operator))
