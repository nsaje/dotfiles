#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.test import TestCase

from utils import url_helper


class FixUrlTest(TestCase):
    def test_fix_url(self):
        url = u'http://www.example.com/inspiration/Seasonal Home-Décor-Projects/?code=tracking code'

        url = url_helper.fix_url(url)

        self.assertEqual(
            url, 'http://www.example.com/inspiration/Seasonal%20Home-D%C3%A9cor-Projects/?code=tracking+code')
