import rest_framework.settings
import rest_framework.throttling
from django.conf import settings


class UserRateOverrideThrottle(rest_framework.throttling.UserRateThrottle):
    override_rates = None

    def __init__(self, *args, **kwargs):
        if not self.override_rates:
            self.override_rates = settings.REST_FRAMEWORK.get("DEFAULT_OVERRIDE_THROTTLE_RATES")
        return super().__init__(*args, **kwargs)

    def allow_request(self, request, view):
        if request.user.email.endswith("@service.zemanta.com"):
            return True
        override_rate = None
        if self.override_rates:
            override_rate = self.override_rates.get(request.user.email, None)
        if override_rate is not None:
            self.num_requests, self.duration = self.parse_rate(override_rate)
        return super().allow_request(request, view)
