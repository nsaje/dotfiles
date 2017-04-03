# -*- coding: utf-8 -*-

from django.db import models


class ReadOnlyModelMixin(object):
    """
    Mixin that disables models.save() and .delete() methods
    """

    def save(self, *args, **kwargs):
        raise AssertionError('Read-only model, save not allowed')

    def delete(self, *args, **kwargs):
        raise AssertionError('Read-only model, delete not allowed')


class ReadOnlyQuerySet(models.QuerySet):
    """
    QuerySet that only allows reading models from db. It does not allow any
    update, insert or delete action.

    NOTE: It does not guard models.save() and .delete() methods. To disable those use the
    ReadOnlyModelMixin mixin.
    """

    def update(self, *args, **kwargs):
        raise AssertionError('Read-only queryset, update not allowed.')

    def delete(self, *args, **kwargs):
        raise AssertionError('Read-only queryset, delete not allowed.')

    def create(self, *args, **kwargs):
        raise AssertionError('Read-only queryset, create not allowed.')

    def get_or_create(self, *args, **kwargs):
        raise AssertionError('Read-only queryset, get_or_create not allowed.')

    def bulk_create(self, *args, **kwargs):
        raise AssertionError('Read-only queryset, bulk_create not allowed.')
