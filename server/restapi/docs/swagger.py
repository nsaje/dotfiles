from drf_yasg.generators import OpenAPISchemaGenerator


class RestAPISchemaGenerator(OpenAPISchemaGenerator):
    def __init__(self, info, version="", url=None, patterns=None, urlconf=None):
        super().__init__(info, version, url, patterns, urlconf)

    def get_endpoints(self, request):
        endpoints = super().get_endpoints(request)
        return {endpoint: content for endpoint, content in endpoints.items() if "v1" in endpoint}
