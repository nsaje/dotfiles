-- TODO should be 'conversion_count'
SUM(CASE WHEN {{ p }}slug='{{ goal_id }}' THEN hits ELSE 0 END) {{ alias }}