import collections
from dataclasses import dataclass

import backtosql

KW_DIMENSIONS = "kw::dimensions"
KW_AGGREGATES = "kw::aggregates"
KW_END = "kw::end"


@dataclass
class ColumnDefinition:
    definition: str
    is_dimension: bool

    def __str__(self):
        return self.definition


def generate_table_definition(
    table_name, table_definition_stream, breakdown, sortkey, distkey=None, diststyle="key", breakdown_overrides=None
):
    column_definitions = parse_table_definition(table_definition_stream)
    columns_to_include = _narrow_to_breakdown(column_definitions, breakdown, breakdown_overrides)

    return backtosql.generate_sql(
        "etl_create_table.sql",
        dict(
            table_name=table_name,
            column_definitions=columns_to_include,
            sortkey=sortkey,
            distkey=distkey,
            diststyle=diststyle,
        ),
    )


def generate_table_definition_postgres(
    table_name, table_definition_stream, breakdown, index, dependencies, breakdown_overrides=None
):
    column_definitions = parse_table_definition(table_definition_stream)
    columns_to_include = _narrow_to_breakdown(column_definitions, breakdown, breakdown_overrides)

    return backtosql.generate_sql(
        "etl_create_table_postgres.sql",
        dict(table_name=table_name, column_definitions=columns_to_include, index=index, dependencies=dependencies),
    )


def parse_table_definition(stream):
    column_definitions = collections.OrderedDict()

    dimensions_follow = False
    aggregates_follow = False
    for line in stream.readlines():
        if KW_END in line:
            break

        if KW_DIMENSIONS in line:
            dimensions_follow = True
            aggregates_follow = False
            continue
        if KW_AGGREGATES in line:
            dimensions_follow = False
            aggregates_follow = True
            continue

        if not (dimensions_follow or aggregates_follow):
            continue

        line = line.strip().replace(",", "")
        if not line:
            continue

        name = line.split(" ")[0]
        column_definitions[name] = ColumnDefinition(definition=line, is_dimension=dimensions_follow)

    return column_definitions


def _narrow_to_breakdown(column_definitions, breakdown, breakdown_overrides=None):
    if breakdown_overrides:
        for column_name, definition in list(breakdown_overrides.items()):
            column_definitions[column_name].definition = definition

    return [col for col_name, col in column_definitions.items() if not col.is_dimension or col_name in breakdown]
