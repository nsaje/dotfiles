class ConstraintTempTable(object):
    def __init__(self, table_name, constraint, values):
        if not values:
            # if there are no values we can't determine column type
            raise ValueError("Cannot create a temporary table with no values")
        self.name = table_name
        self.constraint = constraint
        self.values = values
        self.values_insert_template = self._get_values_insert_template(values)
        self.values_type = self._get_values_type(values)

    @staticmethod
    def _get_values_insert_template(values):
        return ", ".join(["(%s)"] * len(values))

    @staticmethod
    def _get_values_type(values):
        if isinstance(values[0], str):
            return 'text'
        elif isinstance(values[0], int):
            return 'int'

    def __hash__(self):
        return hash(self.name)
