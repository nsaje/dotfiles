from . import helpers
from .columns import TemplateColumn


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


class Model(object, metaclass=ModelMeta):
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

    def __init__(self):
        self.columns = self.__COLUMNS__[:]
        self.columns_dict = {k: v for k, v in self.__COLUMNS_DICT__.items()}

    def get_columns(self):
        return self.columns

    def get_column(self, alias):
        alias = helpers.clean_alias(alias)
        if alias not in self.columns_dict:
            raise helpers.BackToSQLException(
                "Column for alias '{}' does not exist".format(alias))

        return self.columns_dict[helpers.clean_alias(alias)]

    def has_column(self, alias):
        return helpers.clean_alias(alias) in self.columns_dict

    def select_columns(self, subset=None, group=None):
        if subset is not None:
            columns = []
            unknown = []

            for alias in subset:
                alias = helpers.clean_alias(alias)
                if alias in self.columns_dict:
                    columns.append(self.columns_dict[alias])
                else:
                    unknown.append(alias)

            if unknown:
                raise helpers.BackToSQLException('Unknown columns in subset {}'.format(unknown))

        else:
            columns = [x for x in self.get_columns()]

        if group:
            columns = [x for x in columns if x.group == group]

        return columns

    def select_order(self, subset):
        return [self.get_column(c).as_order(c) for c in subset]

    def add_column(self, column):
        self.columns.append(column)
        self.columns_dict[column.alias] = column

        setattr(self, column.alias, column)
