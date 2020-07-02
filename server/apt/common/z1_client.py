import base64
import json

import requests

from utils import zlogging

logger = zlogging.getLogger(__name__)

Z1_IDENTITY_MANAGEMENT_SERVICE_URL = "https://oneapi.zemanta.com"


class Z1APIException(Exception):
    pass


class Z1Client(object):
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret

        self._access_token = None

    def make_api_call(self, url, method="POST", headers=None, params=None, data=None):
        if not headers:
            headers = {}

        self._refresh_access_token()
        headers.update({"Authorization": "Bearer {access_token}".format(access_token=self._access_token)})

        json_body = None
        if data is not None:
            headers.update({"Content-type": "application/json"})
            headers.update({"Accept": "application/json"})
            json_body = json.dumps(data).encode("utf-8")

        return self._execute_request(url, method=method, headers=headers, params=params, data=json_body)

    def _refresh_access_token(self):
        if self._access_token is None:
            self._access_token = self._get_access_token()

    def _get_access_token(self):
        url = "{z1_identity_management_service_url}/o/token/".format(
            z1_identity_management_service_url=Z1_IDENTITY_MANAGEMENT_SERVICE_URL
        )

        headers = {}
        headers.update(
            {
                "Authorization": "Basic {}".format(
                    base64.b64encode((self.client_id + ":" + self.client_secret).encode("utf-8")).decode("utf-8")
                )
            }
        )
        headers.update({"Content-type": "application/x-www-form-urlencoded"})
        params = {"grant_type": "client_credentials"}

        response = self._execute_request(url, params=params, headers=headers)
        response_body = response.json()

        if response.status_code != 200:
            raise Z1APIException(
                "Request {url} failed. Status code: {status_code}. Response body: {response_body}.".format(
                    url=url, status_code=response.status_code, response_body=response.json()
                )
            )

        return response_body.get("access_token")

    @staticmethod
    def _execute_request(url, method="POST", headers=None, params=None, data=None):
        try:
            response = requests.request(
                method, url, headers=headers if headers else {}, params=params if params else {}, data=data
            )
        except requests.exceptions.RequestException as exception:
            logger.exception(exception)
            response = exception

        return response
