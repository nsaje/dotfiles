# -*- coding: utf-8 -*-
import os

import xlsxwriter

import redshiftapi.db
import dash.constants

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
        seq.i > 0 AND seq.i <= (CHAR_LENGTH(bluekai_categories) - CHAR_LENGTH(REPLACE(bluekai_categories, ',', ''))) + 1
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
        seq.i > 0 AND seq.i <= (CHAR_LENGTH(bluekai_categories) - CHAR_LENGTH(REPLACE(bluekai_categories, ',', ''))) + 1
)
SELECT
    CASE category
        WHEN 765427 THEN 'Age Broad > 21-29'
        WHEN 765428 THEN 'Age Broad > 30-39'
        WHEN 765429 THEN 'Age Broad > 40-49'
        WHEN 765430 THEN 'Age Broad > 50-64'
        WHEN 765431 THEN 'Age Broad > 65+'
        WHEN 765446 THEN 'Education > Graduate Degree'
        WHEN 765447 THEN 'Education > High School Diploma'
        WHEN 765448 THEN 'Education > Some College'
        WHEN 765449 THEN 'Education > Some Graduate School'
        WHEN 765450 THEN 'Education > Undergraduate Degree'
        WHEN 765466 THEN 'Household Income (USD) > Less than $20,000'
        WHEN 765461 THEN 'Household Income (USD) > $20,000 - $49,999'
        WHEN 765463 THEN 'Household Income (USD) > $50,000 - $74,999'
        WHEN 765465 THEN 'Household Income (USD) > $75,000 - $99,999'
        WHEN 765459 THEN 'Household Income (USD) > $100,000 - $149,999'
        WHEN 765460 THEN 'Household Income (USD) > $150,000 - $249,999'
        WHEN 765462 THEN 'Household Income (USD) > $250,000 - $499,999'
        WHEN 765464 THEN 'Household Income (USD) > $500,000+'
        WHEN 765487 THEN 'Gender > Female'
        WHEN 765488 THEN 'Gender > Male'
        WHEN 765569 THEN 'Marital Status > Co-Habiting'
        WHEN 765570 THEN 'Marital Status > Married'
        WHEN 765571 THEN 'Marital Status > Separated/Divorced'
        WHEN 765572 THEN 'Marital Status > Single'
        WHEN 839865 THEN 'Hobbies & Interests > Beauty & Style'
        WHEN 839877 THEN 'Hobbies & Interests > Education & Career'
        WHEN 839887 THEN 'Hobbies & Interests > Health & Fitness'
        WHEN 839898 THEN 'Hobbies & Interests > Hobbies'
        WHEN 839916 THEN 'Hobbies & Interests > Home & Garden'
        WHEN 839925 THEN 'Hobbies & Interests > Internet & Online Activities'
        WHEN 839932 THEN 'Hobbies & Interests > Outdoor Activities'
        WHEN 839945 THEN 'Hobbies & Interests > Parenting & Family'
        WHEN 839953 THEN 'Hobbies & Interests > Pets'
        WHEN 839958 THEN 'Hobbies & Interests > Politics & Society'
        WHEN 839994 THEN 'Hobbies & Interests > Science & Humanities'
        WHEN 840001 THEN 'Hobbies & Interests > Shopping'
        WHEN 765452 THEN 'Employment Status > Employed'
        WHEN 840031 THEN 'Education & Career > Beginning Career'
        WHEN 840033 THEN 'Education & Career > College Life'
        WHEN 840034 THEN 'Education & Career > Graduating'
        WHEN 840035 THEN 'Education & Career > Graduating College'
        WHEN 840036 THEN 'Education & Career > Job Seekers'
        WHEN 840037 THEN 'Education & Career > Retirees'
        WHEN 840039 THEN 'Family & Children > Empty Nesters'
        WHEN 840040 THEN 'Family & Children > Expectant Parents'
        WHEN 840042 THEN 'Family & Children > New Parents'
        WHEN 840063 THEN 'Getting Married'
        WHEN 840064 THEN 'Getting Married > Wedding Planning'
        WHEN 840060 THEN 'Moving'
        WHEN 840061 THEN 'Moving > New Movers'
        WHEN 840062 THEN 'Moving > Pre Movers'
        WHEN 840071 THEN 'Lifestyles > Discretionary Spenders'
        WHEN 840084 THEN 'Lifestyles > Enthusiasts'
        WHEN 840094 THEN 'Lifestyles > Millennials'
        WHEN 840106 THEN 'Lifestyles > Moms'
        WHEN 840125 THEN 'Lifestyles > Parents'
        WHEN 671925 THEN 'Travel'
        WHEN 687086 THEN 'Travel > In-Market'
        WHEN 679835 THEN 'Travel > Interest'
        WHEN 778545 THEN 'Autos'
        WHEN 780418 THEN 'Autos > In-Market'
        WHEN 779615 THEN 'Autos > Interest'
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
        data['verticals'] = [
            (dash.constants.InterestCategory.get_text(k) or k, v) for k, v in c.fetchall()
        ]
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
        for listname, rows in data.items():
            worksheet = workbook.add_worksheet(listname)
            for r, columns in enumerate(rows):
                for c, cell in enumerate(columns):
                    worksheet.write(r, c, cell)
        workbook.close()
    return filepath
