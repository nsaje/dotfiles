TYPE_MAP = {
    "int": "pyspark.sql.types.IntegerType()",
    "long": "pyspark.sql.types.LongType()",
    "decimal": "pyspark.sql.types.DecimalType({}, {})",
    "string": "pyspark.sql.types.StringType()",
}

STRUCT_TEMPLATE = "pyspark.sql.types.StructType([{columns}])"
FIELD_TEMPLATE = 'pyspark.sql.types.StructField("{name}", {type}, {nullable})'


class Column:
    def __init__(self, name, typ, *type_args, nullable=False):
        self.name = name
        self.type = typ
        self.type_args = type_args
        self.nullable = nullable

    def __str__(self):
        return FIELD_TEMPLATE.format(
            name=self.name, type=TYPE_MAP[self.type].format(*self.type_args), nullable=self.nullable
        )


def generate_schema(columns):
    formatted_columns = [str(column) for column in columns]
    return STRUCT_TEMPLATE.format(columns=", ".join(formatted_columns))
