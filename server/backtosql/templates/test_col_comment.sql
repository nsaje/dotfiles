{% load backtosql_tags %}
-- some random comment before
/*
Block comment
*/
SUM({{ p }}{{ column_name }})*{{ multiplier }}{{ alias|as_kw }} -- ending comment
-- another comment following