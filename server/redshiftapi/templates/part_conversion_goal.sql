{% load postgres_tags %}
-- Here goal_id is a string that is unsanitized user input. This is bad practice.
-- The reality is that we're currently tracking goals in the `conversions` table by user-defined slugs, 
-- even though they should have had their own internal ids.

-- Still, all user input should be put into queries via parametrization, but in this case since it's a
-- case of dynamic columns, it'd be difficult to implement since at this point we're just building the
-- model, not the query.
SUM (CASE WHEN {{ p }}slug={{ goal_id|pg_quote_escape_string_literal }} THEN conversion_count ELSE 0 END) {{ alias }}