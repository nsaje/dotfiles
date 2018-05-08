from django.core.paginator import Paginator
from django.db import connections


class SaveWithRequestMixin(object):
    def save_model(self, request, obj, form, change):
        obj.save(request)


# source: https://medium.com/squad-engineering/estimated-counts-for-faster-django-admin-change-list-963cbf43683e
class LargeTablePaginator(Paginator):
    """
    Warning: Postgresql only hack
    Overrides the count method of QuerySet objects to get an estimate instead of actual count when not filtered.
    However, this estimate can be stale and hence not fit for situations where the count of objects actually matter.
    """
    def _get_count(self):
        if getattr(self, '_count', None) is not None:
            return self._count

        query = self.object_list.query
        if not query.where:
            try:
                cursor = connections[self.object_list.db].cursor()
                cursor.execute("SELECT reltuples FROM pg_class WHERE relname = %s",
                               [query.model._meta.db_table])
                self._count = int(cursor.fetchone()[0])
            except Exception:
                self._count = super(LargeTablePaginator, self).count
        else:
            self._count = super(LargeTablePaginator, self).count

        return self._count

    count = property(_get_count)
