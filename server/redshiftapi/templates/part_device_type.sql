CASE
    WHEN {{ p }}device_type == 4 THEN 3  -- mobile
    WHEN {{ p }}device_type == 2 THEN 1  -- desktop
    WHEN {{ p }}device_type == 5 THEN 2  -- tablet
    ELSE 0 -- undefined
END {{ p }}{{ alias }}
