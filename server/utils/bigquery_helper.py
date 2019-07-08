from django.conf import settings
from google.cloud import bigquery
from google.oauth2 import service_account


def query(query, timeout=None, **query_kwargs):
    job_config = bigquery.QueryJobConfig(**query_kwargs)
    job = _get_client().query(query, job_config=job_config)
    return job.result(timeout)


def upload_file(bytes_stream, dataset_name, table_name, timeout=None, **load_kwargs):
    bigquery_client = _get_client()
    dataset = bigquery_client.dataset(dataset_name)
    table = dataset.table(table_name)
    job_config = bigquery.LoadJobConfig(**load_kwargs)

    job = bigquery_client.load_table_from_file(bytes_stream, table, job_config=job_config)
    job.result(timeout)


def upload_csv_file(bytes_stream, dataset_name, table_name, **load_kwargs):
    upload_file(bytes_stream, dataset_name, table_name, source_format=bigquery.job.SourceFormat.CSV, **load_kwargs)


def _get_client():
    credentials = service_account.Credentials.from_service_account_info(settings.BIGQUERY_CREDENTIALS)
    return bigquery.Client(project=settings.BIGQUERY_CREDENTIALS.get("project_id"), credentials=credentials)
