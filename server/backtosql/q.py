import logging

from backtosql import helpers
from utils import cache_helper

logger = logging.getLogger(__name__)


def dissect_constraint_key(constraint_key):
    return constraint_key.split('__')


class Q(object):
    '''
    Used for constructing the WHERE filter of the query that supports AND, OR and NOT,
    similar to django Q (https://github.com/django/django/blob/master/django/db/models/query_utils.py)
    '''

    AND = ' AND '
    OR = ' OR '
    MAX_RECURSION_DEPTH = 900

    def __init__(self, model, *args, **kwargs):
        self.negate = False
        self.join_operator = self.AND
        self.children = list(args) + sorted(list(kwargs.iteritems()))
        self.model = model
        self.use_tmp_tables = False

        # cache, used to preserve the order of parameters
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

    def was_generated(self):
        return self.params is not None

    def generate(self, prefix=None):
        if self.prefix is not None and self.prefix != prefix:
            raise helpers.BackToSQLException("Only 1 prefix per Q")
        self.prefix = prefix

        self.query, self.params, self.tmp_tables = self._generate(prefix, self.use_tmp_tables)

        return self.query

    @classmethod
    def none(cls, model):
        # similar as to how django queryset none() works
        return cls(model, __none=None)

    def get_params(self):
        if not self.was_generated():
            raise helpers.BackToSQLException("Query not yet generated")
        return self.params

    def get_create_tmp_tables(self):
        if not self.was_generated():
            raise helpers.BackToSQLException("Query not yet generated")
        if len(self.tmp_tables) == 0:
            return None
        params = [param for table in self.tmp_tables for param in table[1]]
        return helpers.generate_sql('tmp_tables.sql', {'tmp_tables': self.tmp_tables}), params

    def get_drop_tmp_tables(self):
        if not self.was_generated():
            raise helpers.BackToSQLException("Query not yet generated")
        if len(self.tmp_tables) == 0:
            return None
        return helpers.generate_sql('tmp_tables_cleanup.sql', {'tmp_tables': self.tmp_tables}), []

    def _generate(self, prefix, use_tmp_tables, depth=1):
        if depth >= self.MAX_RECURSION_DEPTH:
            # This code would overflow the stack in case there are too many
            # nested WHERE conditions. This is a limit defined by max recursion
            # limit on your system. Anyway if you reach this limit try to redesign
            # your logics so it won't generate a tree so deep.
            raise helpers.BackToSQLException("Q recursion too deep {}".format(self.MAX_RECURSION_DEPTH))

        parts = []
        params = []
        tmp_tables = []

        for child in self.children:
            if isinstance(child, type(self)):
                child_parts, child_params, child_tables = child._generate(prefix, use_tmp_tables, depth + 1)
            else:
                child_parts, child_params, child_tables = self._generate_sql(child, prefix, use_tmp_tables)

            parts.append(child_parts)
            params.extend(child_params)
            tmp_tables.extend(child_tables)

        if not parts and not params:
            return '1=1', [], []

        ret = '(' + self.join_operator.join(parts) + ')'
        if self.negate:
            ret = 'NOT ' + ret

        return ret, params, tmp_tables

    def _prepare_constraint(self, constraint):
        constraint_name, value = constraint

        parts = dissect_constraint_key(constraint_name)
        alias = helpers.clean_alias(parts[0])

        if len(parts) == 2:
            operator = parts[1]
        else:
            operator = "eq"

        if alias == '':
            return None, operator, value

        column = self.model.get_column(alias)
        return column, operator, value

    def _generate_sql(self, constraint, prefix, use_tmp_tables):
        column, operator, value = self._prepare_constraint(constraint)

        operator_dict = {
            "lte": '{}<=%s',
            "lt": '{}<%s',
            "gte": '{}>=%s',
            "gt": '{}>%s',
        }

        if operator == 'none':
            return "1=%s", [2], []

        if operator in operator_dict:
            return operator_dict[operator].format(column.only_column(prefix)), [value], []
        elif operator == "eq":
            if helpers.is_collection(value):
                if not value:
                    return 'FALSE', [], []
                if use_tmp_tables:
                    if isinstance(value[0], int) or isinstance(value[0], basestring):
                        tmp_table_name = 'tmp_filter_{}_{}'.format(column.only_column(),
                                                                   cache_helper.get_cache_key(value))[:63]
                        return '{} IN (SELECT id FROM {})'.format(
                            column.only_column(prefix),
                            tmp_table_name,
                        ), [], [(tmp_table_name, value)]
                    else:
                        logger.warning('Invalid type %s for temp tables, using x=ANY()', type(value[0]).__name__)
                return '{}=ANY(%s)'.format(column.only_column(prefix)), [value], []

            if value is None:
                return '{} IS %s'.format(column.only_column(prefix)), [value], []
            return '{}=%s'.format(column.only_column(prefix)), [value], []

        elif operator == "neq":
            if helpers.is_collection(value):
                if value:
                    return '{}!=ANY(%s)'.format(column.only_column(prefix)), [value], []

                return 'TRUE', [], []

            if value is None:
                return '{} IS NOT %s'.format(column.only_column(prefix)), [value], []

            return '{}!=%s'.format(column.only_column(prefix)), [value], []

        raise helpers.BackToSQLException("Unknown constraint type: {}".format(operator))
