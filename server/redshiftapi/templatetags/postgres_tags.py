import psycopg2.extensions
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def pg_quote_escape_string_literal(value):
    # quote the string correctly, enclosing it with single quotes and escaping any single quotes inside
    quoted = psycopg2.extensions.QuotedString(value.encode("utf-8")).getquoted().decode("utf-8")
    # escape % sign since we're building a parametrized query
    escaped = quoted.replace("%", "%%")
    # mark as safe so django templating doesn't do additional HTML escaping
    return mark_safe(escaped)
