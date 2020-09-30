COALESCE({{ p }}publisher, '') || '__' || {{ p }}source_id || '__' || COALESCE({{ p }}placement, '') {{ alias }}
