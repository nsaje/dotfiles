{% autoescape off %}

SELECT create_hypertable('{{ table_name }}', 'date', chunk_time_interval => INTERVAL '1 day');

{% endautoescape %}
