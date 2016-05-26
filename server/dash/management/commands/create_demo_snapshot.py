import argparse
from django.db import models
import django

from utils.command_helpers import ExceptionCommand

import sys
try:
    import json
except ImportError:
    from django.utils import simplejson as json

try:
    from django.db.models import loading
except ImportError:
    from django.apps import apps as loading
from django.core.serializers import serialize
from django.conf import settings
from django.template import Variable, VariableDoesNotExist


import logging
logger = logging.getLogger(__name__)


class Command(ExceptionCommand):
    help = """ Create a DB snapshot for demo deploys. """

    def handle(self, *args, **options):
        # dump_name = 'dash.adgroup'
        dump_name = 'dash.account'
        # pks = [1842]
        pks = [308]
        dump_settings = settings.CUSTOM_DUMPS[dump_name]
        (app_label, model_name) = dump_settings['primary'].split('.')
        dump_me = loading.get_model(app_label, model_name)
        objs = dump_me.objects.filter(pk__in=[int(i) for i in pks])
        for obj in objs:
            add_object_dependencies(obj, dump_settings['dependents'])
        # add_to_serialize_list(objs)

        serialize_fully()
        data = serialize('json', [o for o in serialize_me if o is not None],
                         use_natural_foreign_keys=True, use_natural_primary_keys=True)

        self.stdout.write(data)


serialize_me = []
seen = {}


def get_fields(obj):
    try:
        return obj._meta.fields
    except AttributeError:
        return []


def get_many_to_many_fields(obj):
    try:
        return obj._meta.many_to_many
    except AttributeError:
        return []


def serialize_fully():
    index = 0
    while index < len(serialize_me):
        for field in get_fields(serialize_me[index]):
            logger.info(str(serialize_me[index]) + ': ' + str(field))
            if isinstance(field, models.ForeignKey):
                add_to_serialize_list(
                    [serialize_me[index].__getattribute__(field.name)])
        for field in get_many_to_many_fields(serialize_me[index]):
            logger.info(str(serialize_me[index]) + '; ' + str(field))
            add_to_serialize_list(
                serialize_me[index].__getattribute__(field.name).all())
        index += 1

    serialize_me.reverse()


def add_to_serialize_list(objs):
    for obj in objs:
        logger.info("add_to_serialize_list: obj: " + str(obj))
        if obj is None:
            continue
        if not hasattr(obj, '_meta'):
            add_to_serialize_list(obj)
            continue

        # Proxy models don't serialize well in Django.
        if obj._meta.proxy:
            obj = obj._meta.proxy_for_model.objects.get(pk=obj.pk)
        model_name = getattr(obj._meta, 'model_name',
                             getattr(obj._meta, 'module_name', None))
        key = "%s:%s:%s" % (obj._meta.app_label, model_name, obj.pk)

        if key not in seen:
            serialize_me.append(obj)
            seen[key] = 1
        else:  # move to end
            logger.info("MOVING TO END: " + str(obj))
            idx = serialize_me.index(obj)
            serialize_me[idx] = None
            serialize_me.append(obj)


def add_object_dependencies(obj, dependencies):
    # get the dependent objects and add to serialize list
    for dep in dependencies:
        try:
            if isinstance(dep, dict):
                sub_deps = dep['dependents']
                dep = dep['primary']
            else:
                sub_deps = None

            thing = Variable("thing.%s" % dep).resolve({'thing': obj})
            add_to_serialize_list([thing])
            if sub_deps:
                for new_obj in thing:
                    add_object_dependencies(new_obj, sub_deps)
        except VariableDoesNotExist:
            sys.stderr.write('%s not found' % dep)

    if not dependencies:
        add_to_serialize_list([obj])
