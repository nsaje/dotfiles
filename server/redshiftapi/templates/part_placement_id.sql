MAX(CONCAT({{ p }}publisher_source_id, CONCAT('__', COALESCE({{ p }}placement, '')))) {{ alias }}
