{% load backtosql_tags %}
{% autoescape off %}

SELECT COUNT(DISTINCT(zuid))
FROM pixie_sample
WHERE
     account_id = %s AND
     slug = %s AND
     timestamp > %s
         {% if rules %}
             AND (
             {% for rule in rules %}
                  {% for val in rule.values %}
                      {% if rule.type == rule_type.STARTS_WITH %}
                          referer ILIKE %s + '%%'
                      {% elif rule.type == rule_type.CONTAINS %}
                          referer ILIKE '%%' + %s + '%%'
                      {% elif rule.type == rule_type.NOT_STARTS_WITH %}
                          referer NOT ILIKE %s + '%%'
                      {% elif rule.type == rule_type.NOT_CONTAINS %}
                          referer NOT ILIKE '%%' + %s + '%%'
                      {% endif %}
                      {% if not forloop.last %}
                          OR
                      {% endif %}
                  {% endfor %}
                  {% if not forloop.last %}
                      OR
                  {% endif %}
             {% endfor %}
          )
          {% endif %}
{% endautoescape %}
