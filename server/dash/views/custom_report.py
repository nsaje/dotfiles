# -*- coding: utf-8 -*-

from dash.common.views_base import DASHAPIBaseView
from utils import zlogging

logger = zlogging.getLogger(__name__)


class ExportApiView(DASHAPIBaseView):
    def dispatch(self, request, *args, **kwargs):
        try:
            return super(DASHAPIBaseView, self).dispatch(request, *args, **kwargs)
        except Exception as e:
            return self.get_exception_response(request, e)
