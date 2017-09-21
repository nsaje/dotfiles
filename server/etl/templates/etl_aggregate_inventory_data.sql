INSERT INTO mv_inventory (
    SELECT
        country,
        publisher,
        device_type,
        SUM(bid_reqs),
        SUM(bids),
        SUM(win_notices),
        SUM(total_win_price)

    FROM supply_stats

    WHERE date BETWEEN %(date_from)s AND %(date_to)s

    GROUP BY country, publisher, device_type

    ORDER BY country, publisher, device_type
);
