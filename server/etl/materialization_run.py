import datetime

from utils import dates_helper

from . import models


def create_done():
    models.MaterializationRun.objects.create()


def get_latest():
    return models.MaterializationRun.objects.last()


def get_latest_finished_dt():
    latest = get_latest()
    if latest is None:
        return None
    return latest.finished_dt


def materialization_completed_for_local_today() -> bool:
    # after EST midnight wait 2h for data to be available + 3h for refresh_etl to complete
    from_date_time = dates_helper.local_midnight_to_utc_time().replace(tzinfo=None) + datetime.timedelta(hours=5)
    return models.MaterializationRun.objects.filter(finished_dt__gte=from_date_time).exists()
