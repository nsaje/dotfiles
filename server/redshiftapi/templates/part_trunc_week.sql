-- TODO note this is monday-based, not start_date based
DATE_TRUNC('week', {{ p }}{{ column_name }}) {% if alias %} AS {{ alias }} {% endif %}