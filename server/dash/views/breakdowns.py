from utils import exc
from utils import api_common


class BreakdownView(api_common.BaseApiView):
    def get(self, request, level_, id_, breakdown):
        # check permissions
        # clean query parameters
        # validate breakdown is supported
        # validate breakdown size
        # execute the breakdown
        # convert results to format suitable for resposne

        return self.create_api_response({})