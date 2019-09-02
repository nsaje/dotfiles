"""
WSGI config for server project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/dev/howto/deployment/wsgi/
"""
# isort:skip_file
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

import gevent.socket
import socket
import swinfra.wsgi
import utils.profiler

if socket.socket is gevent.socket.socket:  # if running in gevent
    import psycogreen.gevent

    psycogreen.gevent.patch_psycopg()

from django.core.wsgi import get_wsgi_application


application = swinfra.wsgi.OutbrainWSGI(get_wsgi_application())
