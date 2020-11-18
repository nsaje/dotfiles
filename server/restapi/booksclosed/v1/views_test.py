import datetime

import mock
from django.urls import reverse

from restapi.common.views_base_test_case import RESTAPITestCase


class BooksClosedSetTest(RESTAPITestCase):
    @mock.patch(
        "etl.materialization_run.get_last_books_closed_date",
        mock.MagicMock(return_value=datetime.datetime(2000, 1, 1, 12)),
    )
    def test_get(self):
        r = self.client.get(reverse("restapi.booksclosed.v1:booksclosed"))
        resp_json = self.assertResponseValid(r)
        self.assertEqual(
            resp_json["data"]["trafficData"]["latestCompleteDate"],
            datetime.datetime(2000, 1, 1, 12).strftime("%Y-%m-%d"),
        )
