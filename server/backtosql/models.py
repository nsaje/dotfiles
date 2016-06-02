import helpers
import q
from columns import TemplateColumn


class ModelMeta(type):
    """
    ModelMeta is a meta class of Model. It takes care for class columns initialization.
    """
    def __new__(cls, name, parents, dct):
        model_class = super(ModelMeta, cls).__new__(cls, name, parents, dct)

        # Important: this initializes alias names from python attribute names
        # This is the main functionality of the model
        model_class._init_column_aliases()
        return model_class


class Model(object):
    __metaclass__ = ModelMeta

    __COLUMNS__ = None
    __COLUMNS_DICT__ = None

    @classmethod
    def _init_column_aliases(cls):
        """
        Gets alias names from python attributes and sets alias attributes
        on TemplateColumn with those names.
        """

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

            if unknown:
                raise helpers.BackToSQLException('Unknown columns in subset {}'.format(unknown))

        else:
            columns = cls.get_columns()

        if group:
            columns = [x for x in columns if x.group == group]

        return columns

    @classmethod
    def select_order(cls, subset):
        return [cls.get_column(c).as_order(c) for c in subset]
