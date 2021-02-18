# isort:skip_file
import os
import swinfra.celery

from celery import Celery  # noqa

from django.conf import settings  # noqa

from django.db.backends.signals import connection_created
from django.contrib.postgres.signals import register_type_handlers

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

app = Celery("eins")

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# This is a workaround to be able to use django.contrib.postgres app that registers (unneeded) signals
# which cause an db exception to be thrown due to suspected django bug
connection_created.disconnect(register_type_handlers)

swinfra.celery.outbrain_celery_setup()
