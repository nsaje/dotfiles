# isort:skip_file
import os
import swinfra.celery

from celery import Celery  # noqa

from django.conf import settings  # noqa

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

app = Celery("eins")

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

swinfra.celery.outbrain_celery_setup()
