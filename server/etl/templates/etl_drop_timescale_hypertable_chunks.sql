{% autoescape off %}

SELECT drop_chunks(INTERVAL '{{ keep_days }} days', '{{ table_name }}');

{% endautoescape %}
