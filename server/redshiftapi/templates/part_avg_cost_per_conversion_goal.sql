-- NOTE 1: fields from multiple table that is why no prefix as backtosql does not support
-- multiple aliases in 1 column
-- NOTE 2: Not an aggregates its just an calculation on already aggregated fields
cost / NULLIF({{ conversion_key }}, 0) {{ alias }}