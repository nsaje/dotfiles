{% load backtosql_tags %}
-- some random comment before
/*
Block comment
*/
SUM({{ p }}{{ column_name }})*{{ multiplier }}{{ alias|lspace }} -- ending comment
-- another comment following