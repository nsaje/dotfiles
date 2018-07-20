# -*- coding: utf-8 -*-

from django.db import models


class FootprintModel(models.Model):
    def __init__(self, *args, **kwargs):
        super(FootprintModel, self).__init__(*args, **kwargs)
        if not self.pk:
            return
        self._footprint()

    def _get_value_fieldname(self, fieldname):
        field = self._meta.get_field(fieldname)
        if field.many_to_one:
            return field.attname
        return fieldname

    def has_changed(self, field=None):
        if not self.pk:
            return False
        if field:
            return self._orig[field] != getattr(self, self._get_value_fieldname(field))
        for f in self._meta.fields:
            if self._orig[f.name] != getattr(self, self._get_value_fieldname(f.name)):
                return True
        return False

    def previous_value(self, fieldname):
        field = self._meta.get_field(fieldname)
        if field.many_to_one:
            raise Exception("Previous value not stored as an object")
        return self.pk and self._orig[fieldname]

    def _footprint(self):
        self._orig = {}
        for f in self._meta.fields:
            self._orig[f.name] = getattr(self, self._get_value_fieldname(f.name))

    def save(self, *args, **kwargs):
        super(FootprintModel, self).save(*args, **kwargs)
        self._footprint()

    class Meta:
        abstract = True
