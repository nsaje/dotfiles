import datetime

import django_celery_results.models
from django.test import TestCase

from core.management.commands import clean_up_old_celery_results
from utils.magic_mixer import magic_mixer


class CleanUpOldHistoryStackTracesTest(TestCase):
    def test_delete(self):
        magic_mixer.blend(django_celery_results.models.TaskResult, task_name="TEST")

        old_result = magic_mixer.blend(django_celery_results.models.TaskResult, task_name="TEST")
        old_result.date_created = datetime.datetime(2020, 4, 20)
        old_result.save()
        self.assertEqual(len(django_celery_results.models.TaskResult.objects.filter(task_name="TEST").all()), 2)
        clean_up_old_celery_results.Command._delete_old_data()
        self.assertEqual(len(django_celery_results.models.TaskResult.objects.filter(task_name="TEST").all()), 1)
