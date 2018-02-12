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
