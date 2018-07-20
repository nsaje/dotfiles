from django.conf import settings

from utils import s3helpers
import analytics.statements
import utils.csv_utils
import redshiftapi.db
from dash.features.reports import reports


def upload_report_from_fs(path, filepath):
    s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
    with open(filepath) as fd:
        s3.put(path, fd.read(), human_readable_filename=filepath.split("/")[-1])
    return analytics.statements.get_url(path)


def generate_report_from_dicts(name, dicts):
    """
    Generates a report with keys as column headers
    """

    headers = list(dicts[0].keys())
    headers.sort()

    rows = [headers]
    for row in dicts:
        rows.append([row[h] for h in headers])

    return generate_report(name, rows)


def generate_report(name, data):
    s3 = s3helpers.S3Helper(settings.S3_BUCKET_CUSTOM_REPORTS)
    path = "/custom-csv/{}.csv".format(name)
    s3.put(path, utils.csv_utils.tuplelist_to_csv(data))
    return analytics.statements.get_url(path)


def generate_report_from_query(name, query):
    with redshiftapi.db.get_stats_cursor() as cur:
        cur.execute(query)
        columns = [col[0] for col in cur.description]
        data = cur.fetchall()
        return generate_report(name, [columns] + data)
    return None


def reprocess_report_job(job_id):
    original_job = reports.ReportJob.objects.get(pk=job_id)

    new_job = reports.ReportJob(user=original_job.user, oquery=original_job.query)
    new_job.save()
    reports.ReportJobExecutor(new_job).execute()
    return new_job.result
