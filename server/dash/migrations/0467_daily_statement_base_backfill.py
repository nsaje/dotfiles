# Generated by Django 2.1.11 on 2020-06-19 11:27

from django.db import connection
from django.db import migrations

DAILY_STATEMENT_BASE_BACKFILL_SQL = """
UPDATE
    dash_budgetdailystatement bdsm
SET
    base_media_spend_nano = media_spend_nano,
    base_data_spend_nano = data_spend_nano,
    local_base_media_spend_nano = local_media_spend_nano,
    local_base_data_spend_nano = local_data_spend_nano
WHERE
    bdsm.id BETWEEN %s AND %s;
"""

BATCH_SIZE = 100000


def daily_statement_base_backfill(apps, schema_editor):
    with connection.cursor() as c:
        c.execute("SELECT MAX(id) FROM dash_budgetdailystatement")
        count = c.fetchone()[0] or 0
        for i in range(0, count, BATCH_SIZE):
            c.execute("BEGIN")
            print("Updating ids between %s and %s" % (i, i + BATCH_SIZE))
            c.execute(DAILY_STATEMENT_BASE_BACKFILL_SQL, [i, i + BATCH_SIZE])
            c.execute("COMMIT")


class Migration(migrations.Migration):

    dependencies = [("dash", "0466_auto_20200619_1122")]

    operations = [migrations.RunPython(daily_statement_base_backfill)]