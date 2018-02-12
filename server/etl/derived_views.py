import backtosql


KW_DIMENSIONS = 'kw::dimensions'
KW_AGGREGATES = 'kw::aggregates'
KW_END = 'kw::end'


def generate_table_definition(table_name, table_definition_stream, breakdown, sortkey,
                              distkey=None, diststyle='key', breakdown_overrides=None):
    dimensions, aggregates = parse_table_definition(table_definition_stream)

    if breakdown_overrides:
        for column_name, definition in list(breakdown_overrides.items()):
            dimensions[column_name] = definition

    return backtosql.generate_sql('etl_create_table.sql', dict(
        table_name=table_name,
        dimensions=[dimensions[x] for x in breakdown],
        aggregates=aggregates,
        sortkey=sortkey,
        distkey=distkey,
        diststyle=diststyle
    ))


def generate_table_definition_postgres(table_name, table_definition_stream, breakdown, index,
                                       breakdown_overrides=None):
    dimensions, aggregates = parse_table_definition(table_definition_stream)

    if breakdown_overrides:
        for column_name, definition in list(breakdown_overrides.items()):
            dimensions[column_name] = definition

    return backtosql.generate_sql('etl_create_table_postgres.sql', dict(
        table_name=table_name,
        dimensions=[dimensions[x] for x in breakdown],
        aggregates=aggregates,
        index=index,
    ))


def parse_table_definition(stream):
    dimensions, aggregates = {}, []

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

        line = line.strip().replace(',', '')
        if not line:
            continue

        if dimensions_follow:
            dimension = line.split(' ')[0]
            dimensions[dimension] = line
        if aggregates_follow:
            aggregates.append(line)

    return dimensions, aggregates
