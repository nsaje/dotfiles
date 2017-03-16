import os

import xlsxwriter

import redshiftapi.db

TIME_OF_DAY_UTC = """SELECT date_part('hour', bid_timestamp) as h, count(*) as clicks
FROM audience_report
WHERE
    {key} = {id} AND
    bid_timestamp >= '{gte}' AND bid_timestamp < '{lt}' AND
    blacklisted = ''
GROUP BY h
ORDER BY h;"""

GEOLOCATION = """SELECT country, state, count(*) as clicks
FROM audience_report
WHERE
    {key} = {id} AND
    bid_timestamp >= '{gte}' AND bid_timestamp < '{lt}' AND
    blacklisted = ''
GROUP BY country, state
ORDER BY country, state;"""

VERTICALS = """
WITH exploded_verticals AS (
    SELECT split_part(verticals, ',', seq.i) as vertical
    FROM audience_report, seq_0_to_100 AS seq
    WHERE
        {key} = {id} AND
        bid_timestamp >= '{gte}' AND bid_timestamp < '{lt}' AND
        blacklisted = '' AND
        seq.i > 0 AND seq.i <= (CHAR_LENGTH(verticals) - CHAR_LENGTH(REPLACE(verticals, ',', ''))) + 1
)
SELECT vertical, count(*) as clicks
FROM exploded_verticals
GROUP BY vertical
ORDER BY clicks desc;
"""

BLUEKAI_IDS = """WITH exploded_bluekai AS (
    SELECT split_part(bluekai_categories, ',', seq.i) as category
    FROM audience_report, seq_0_to_100 AS seq
    WHERE
        {key} = {id} AND
        bid_timestamp >= '{gte}' AND bid_timestamp < '{lt}' AND
        blacklisted = '' AND
        seq.i > 0 AND seq.i <= (CHAR_LENGTH(verticals) - CHAR_LENGTH(REPLACE(verticals, ',', ''))) + 1
)
SELECT category, count(*) as clicks
FROM exploded_bluekai
GROUP BY category
ORDER BY clicks desc;"""

BLUEKAI_NAMES = """WITH exploded_bluekai AS (
    SELECT split_part(bluekai_categories, ',', seq.i) as category
    FROM audience_report, seq_0_to_100 AS seq
    WHERE
        {key} = {id} AND
        bid_timestamp >= '{gte}' AND bid_timestamp < '{lt}' AND
        blacklisted = '' AND
        seq.i > 0 AND seq.i <= (CHAR_LENGTH(verticals) - CHAR_LENGTH(REPLACE(verticals, ',', ''))) + 1
)
SELECT
    CASE category
        WHEN 24744 THEN '18-20'
        WHEN 34061 THEN '21-29'
        WHEN 34062 THEN '30-39'
        WHEN 34063 THEN '40-49'
        WHEN 34064 THEN '50-64'
        WHEN 27002 THEN '65-'
        WHEN 22598 THEN 'male'
        WHEN 22599 THEN 'female'
        WHEN 31048 THEN 'Science & Humanities'
        WHEN 67980 THEN 'Other Vehicles'
        WHEN 30943 THEN 'Animals'
        WHEN 25321 THEN 'Video Games'
        WHEN 31089 THEN 'Education'
        WHEN 30741 THEN 'Parenting & Family'
        WHEN 31026 THEN 'Politics & Society'
        WHEN 34077 THEN 'Hobbies Games & Toys'
        WHEN 30732 THEN 'Internet & Online Activities'
        WHEN 30961 THEN 'Business & Finance'
        WHEN 25253 THEN 'News & Current Events'
        WHEN 31020 THEN 'Home & Garden'
        WHEN 25305 THEN 'Food & Drink'
        WHEN 30740 THEN 'Lifestyles'
        WHEN 30957 THEN 'Health Beauty & Style'
        WHEN 14 THEN 'Autos'
        WHEN 25324 THEN 'Personal Finance'
        WHEN 25222 THEN 'Travel'
        WHEN 437522 THEN 'Sports & Recreation'
        WHEN 30739 THEN 'Shopping'
        WHEN 25320 THEN 'Arts & Entertainment'
        WHEN 25315 THEN 'Technology & Computers'
        WHEN 5915 THEN 'Interest'
        WHEN 13771 THEN 'Renters'
        WHEN 75 THEN 'Home Owners'
        WHEN 309722 THEN 'Pre-Movers'
        WHEN 316130 THEN 'New Movers'
        WHEN 356826 THEN 'Employed'
        WHEN 356838 THEN 'Homemaker'
        WHEN 356840 THEN 'Job Seeker'
        WHEN 356843 THEN 'Retired'
        WHEN 234418 THEN '$0-$14999'
        WHEN 234424 THEN '$15000-$19999'
        WHEN 234427 THEN '$20000-$29999'
        WHEN 234430 THEN '$30000-$39999'
        WHEN 234433 THEN '$40000-$49999'
        WHEN 234436 THEN '$50000-$59999'
        WHEN 234439 THEN '$60000-$74999'
        WHEN 234442 THEN '$75000-$99999'
        WHEN 234421 THEN '$100000+'
        WHEN 119781 THEN 'Income Range $250000 and above'
        WHEN 119783 THEN 'Income Range $150000 - $249999'
        WHEN 119785 THEN 'Income Range $125000 - $149999'
        WHEN 119787 THEN 'Income Range $100000 - $124999'
        WHEN 119791 THEN 'Income Range $75000 - $99999'
        WHEN 119793 THEN 'Income Range $60000 - $74999'
        WHEN 119796 THEN 'Income Range $50000 - $59999'
        WHEN 119798 THEN 'Income Range $40000 - $49999'
        WHEN 119800 THEN 'Income Range $30000 - $39999'
        WHEN 119802 THEN 'Income Range $20000 - $29999'
        WHEN 119804 THEN 'Income Range under $20000'
        ELSE 'unknown category: ' + category
END AS category_name, count(*) as clicks
FROM exploded_bluekai
GROUP BY category_name
ORDER BY category_name;"""


def create_report(breakdown, breakdown_id, gte, lt, path='.'):
    data = {}
    params = dict(
        key=breakdown,
        id=breakdown_id,
        gte=str(gte),
        lt=str(lt)
    )
    with redshiftapi.db.get_stats_cursor() as c:
        c.execute(TIME_OF_DAY_UTC.format(**params))
        data['time-of-day-utc'] = c.fetchall()
        c.execute(GEOLOCATION.format(**params))
        data['geolocation'] = c.fetchall()
        c.execute(VERTICALS.format(**params))
        data['verticals'] = c.fetchall()
        c.execute(BLUEKAI_IDS.format(**params))
        data['bluekai-ids'] = c.fetchall()
        c.execute(BLUEKAI_NAMES.format(**params))
        data['bluekai-names'] = c.fetchall()

    filepath = os.path.join(path, 'audience-report_{}-{}_{}_{}.xlsx'.format(
        breakdown,
        breakdown_id,
        str(gte),
        str(lt)
    ))
    with xlsxwriter.Workbook(filepath) as workbook:
        for listname, rows in data.iteritems():
            worksheet = workbook.add_worksheet(listname)
            for r, columns in enumerate(rows):
                for c, cell in enumerate(columns):
                    worksheet.write(r, c, cell)
        workbook.close()
    return filepath
