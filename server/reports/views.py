import datetime
import json
import logging

from utils import api_common
from utils import exc
from utils import statsd_helper

from reports import constants

import dash.models
import reports.models

logger = logging.getLogger(__name__)

class GaContentAdReport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('reports.api', 'gacontentadreport_post')
