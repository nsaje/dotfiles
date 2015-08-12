from utils import api_common
from utils import exc
from utils import statsd_helper


class GaContentAdReport(api_common.BaseApiView):
    @statsd_helper.statsd_timer('reports.api', 'gacontentadreport_post')
    def post(self, request):
        if not request.user.has_perm('zemauth.contentadstats'):
            raise exc.AuthorizationError()




        return self.create_api_response({})
