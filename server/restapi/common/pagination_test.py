from django.test import TestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from dash.models import Account
from utils.magic_mixer import magic_mixer

from .pagination import MarkerOffsetPagination
from .pagination import StandardPagination

factory = APIRequestFactory()


class StandardPaginationTestCase(TestCase):
    def setUp(self):
        magic_mixer.cycle(120).blend(Account)
        self.pagination = StandardPagination()

    def test_no_arguments(self):
        account_qs = Account.objects.order_by("id")
        request = Request(factory.get("/"))
        page = self.pagination.paginate_queryset(Account.objects.all(), request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[:100])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=100&marker={}".format(accounts[-1].id), "data": accounts},
        )

    def test_limit(self):
        account_qs = Account.objects.order_by("id")
        request = Request(factory.get("/", {"limit": 10}))
        page = self.pagination.paginate_queryset(Account.objects.all(), request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[:10])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=10&marker={}".format(accounts[-1].id), "data": accounts},
        )

    def test_custom_default_limit(self):
        account_qs = Account.objects.order_by("id")
        request = Request(factory.get("/"))
        pagination = StandardPagination(default_limit=105, max_limit=1000)
        page = pagination.paginate_queryset(Account.objects.all(), request)
        content = pagination.get_paginated_response(page).data
        accounts = list(account_qs[:105])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=105&marker={}".format(accounts[-1].id), "data": accounts},
        )

    def test_custom_max_limit(self):
        account_qs = Account.objects.order_by("id")
        request = Request(factory.get("/", {"limit": 100}))
        pagination = StandardPagination(max_limit=30, default_limit=50)
        page = pagination.paginate_queryset(Account.objects.all(), request)
        content = pagination.get_paginated_response(page).data
        accounts = list(account_qs[:30])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=30&marker={}".format(accounts[-1].id), "data": accounts},
        )

    def test_marker(self):
        account_qs = Account.objects.order_by("id")
        marker_id = account_qs[9].id
        request = Request(factory.get("/", {"marker": marker_id}))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[10:110])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=100&marker={}".format(accounts[-1].id), "data": accounts},
        )

    def test_marker_first_page(self):
        account_qs = Account.objects.order_by("id")
        request = Request(factory.get("/", {"marker": 0}))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[0:100])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=100&marker={}".format(accounts[-1].id), "data": accounts},
        )

    def test_marker_limit(self):
        account_qs = Account.objects.order_by("id")
        marker_id = account_qs[9].id
        request = Request(factory.get("/", {"marker": marker_id, "limit": 10}))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[10:20])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=10&marker={}".format(accounts[-1].id), "data": accounts},
        )

    def test_offset(self):
        request = Request(factory.get("/", {"offset": 10}))
        page = self.pagination.paginate_queryset(Account.objects.all(), request)
        content = self.pagination.get_paginated_response(page).data
        self.assertDictEqual(
            content,
            {
                "count": 120,
                "next": "http://testserver/?limit=100&offset=110",
                "previous": "http://testserver/?limit=100",
                "data": list(Account.objects.all()[10:110]),
            },
        )

    def test_limit_offset(self):
        request = Request(factory.get("/", {"limit": 10, "offset": 10}))
        page = self.pagination.paginate_queryset(Account.objects.all(), request)
        content = self.pagination.get_paginated_response(page).data
        self.assertDictEqual(
            content,
            {
                "count": 120,
                "next": "http://testserver/?limit=10&offset=20",
                "previous": "http://testserver/?limit=10",
                "data": list(Account.objects.all()[10:20]),
            },
        )


class MarkerOffsetPaginationTestCase(TestCase):
    def setUp(self):
        self.pagination = MarkerOffsetPagination()

    def test_list_no_arguments(self):
        account_qs = [Account(id=x) for x in range(1, 121)]
        request = Request(factory.get("/"))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[:100])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=100&marker={}".format(accounts[-1].id), "data": accounts},
        )

    def test_list_marker(self):
        account_qs = [Account(id=x) for x in range(1, 121)]
        request = Request(factory.get("/", {"marker": 10}))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[10:110])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=100&marker={}".format(accounts[-1].id), "data": accounts},
        )

    def test_list_zero_id(self):
        account_qs = [Account(id=x) for x in range(120)]
        request = Request(factory.get("/"))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[0:100])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=100&marker={}".format(accounts[-1].id), "data": accounts},
        )
        self.assertEqual(accounts[0].id, 0)

    def test_queryset_zero_id(self):
        magic_mixer.cycle(120).blend(Account, id=magic_mixer.sequence(lambda x: str(x)))
        account_qs = Account.objects.order_by("id")
        request = Request(factory.get("/"))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[0:100])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=100&marker={}".format(accounts[-1].id), "data": accounts},
        )
        self.assertEqual(accounts[0].id, 0)

    def test_dict_list_zero_id(self):
        magic_mixer.cycle(120).blend(Account, id=magic_mixer.sequence(lambda x: str(x)))
        account_qs = Account.objects.order_by("id").values("id")
        request = Request(factory.get("/"))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[0:100])
        self.assertDictEqual(
            content,
            {
                "count": 120,
                "next": "http://testserver/?limit=100&marker={}".format(accounts[len(accounts) - 1]["id"]),
                "data": accounts,
            },
        )
        self.assertEqual(accounts[0]["id"], 0)

        account_qs = Account.objects.order_by("pk").values("pk")
        request = Request(factory.get("/"))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[0:100])
        self.assertDictEqual(
            content,
            {
                "count": 120,
                "next": "http://testserver/?limit=100&marker={}".format(accounts[len(accounts) - 1]["pk"]),
                "data": accounts,
            },
        )
        self.assertEqual(accounts[0]["pk"], 0)

    def test_last_page(self):
        account_qs = [Account(id=x) for x in range(120)]
        request = Request(factory.get("/", {"marker": account_qs[99].id}))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[100:120])
        self.assertDictEqual(content, {"count": 120, "next": None, "data": accounts})

    def test_last_whole_page(self):
        account_qs = [Account(id=x) for x in range(120)]
        request = Request(factory.get("/", {"marker": account_qs[19].id}))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        accounts = list(account_qs[20:120])
        self.assertDictEqual(
            content,
            {"count": 120, "next": "http://testserver/?limit=100&marker={}".format(accounts[-1].id), "data": accounts},
        )

    def test_last_empty_page(self):
        account_qs = [Account(id=x) for x in range(120)]
        request = Request(factory.get("/", {"marker": account_qs[119].id}))
        page = self.pagination.paginate_queryset(account_qs, request)
        content = self.pagination.get_paginated_response(page).data
        self.assertDictEqual(content, {"count": 120, "next": None, "data": []})
