import unicodecsv
import datetime
from decimal import Decimal
import StringIO

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from dash import forms


class AdGroupSettingsFormTest(TestCase):
    def setUp(self):
        self.data = {
            'cpc_cc': '0.40',
            'daily_budget_cc': '10.00',
            'end_date': '2014-12-31',
            'id': '248',
            'name': 'Test ad group',
            'start_date': '2014-12-11',
            'state': 2,
            'target_devices': ['desktop', 'mobile'],
            'target_regions': ['US'],
            'tracking_code': 'code=test',
        }

    def test_form(self):
        form = forms.AdGroupSettingsForm(self.data)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {
            'cpc_cc': Decimal('0.40'),
            'daily_budget_cc': Decimal('10.00'),
            'end_date': datetime.date(2014, 12, 31),
            'id': 248,
            'name': 'Test ad group',
            'start_date': datetime.date(2014, 12, 11),
            'state': 2,
            'target_devices': ['desktop', 'mobile'],
            'target_regions': ['US'],
            'tracking_code': 'code=test'
        })


class AdGroupAdsPlusUploadFormTest(TestCase):
    def setUp(self):
        self.batch_name = 'Test batch name'
        self.url = 'http://example.com'
        self.title = 'Test Title'
        self.image_url = 'http://example.com/image'
        self.crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'
        self.display_url = 'example.com'
        self.description = 'testdescription'
        self.brand_name = 'testbrandname'
        self.call_to_action = 'testcalltoaction'

    def test_filetypes(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, {})
        with open('./dash/tests/test.gif') as f:
            valid= form.is_valid_input_file(f.read())
            self.assertFalse(valid)
        with open('./dash/tests/test.jpg') as f:
            valid = form.is_valid_input_file(f.read())
            self.assertFalse(valid)
        with open('./dash/tests/test.xlsx') as f:
            valid = form.is_valid_input_file(f.read())
            self.assertFalse(valid)
        with open('./dash/tests/test.csv') as f:
            valid = form.is_valid_input_file(f.read())
            self.assertTrue(valid)

    def test_no_csv_content(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Crop Areas'], [])
        #    [[self.url, self.title, self.image_url, self.crop_areas]])

        form = self._init_form(csv_file, {'display_url': 'test.com'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'content_ads': [u'Uploaded file is empty.']})

    def test_invalid_display_url(self):
        csv_file = self._get_csv_file(
            ['Url', 'Title', 'Image Url', 'Crop Areas'],
            [[self.url, self.title, self.image_url, self.crop_areas]])

        form = self._init_form(csv_file, {'display_url': 'teststring'})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'display_url': ['Enter a valid URL.']})

    def test_cleaned_display_url(self):
        csv_file = self._get_csv_file(
            ['Url', 'Title', 'Image Url', 'Crop Areas'],
            [[self.url, self.title, self.image_url, self.crop_areas]])

        form = self._init_form(csv_file, {'display_url': 'https://teststring.com/this/'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['display_url'], 'teststring.com/this')

    def test_display_url_over_max_length(self):
        csv_file = self._get_csv_file(
            ['Url', 'Title', 'Image Url', 'Crop Areas'],
            [[self.url, self.title, self.image_url, self.crop_areas]])

        domain = 'aaaaaaaaaaaaaaaaaaaaaa.com'
        self.assertEqual(len(domain), 26, 'domain is not over max length = 25')
        url = 'https://' + domain

        form = self._init_form(csv_file, {'display_url': url})

        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors, {'display_url': ['Display URL is too long (26/25).']})

    def test_form(self):
        csv_file = self._get_csv_file(
            ['Url', 'Title', 'Image Url', 'Crop Areas'],
            [[self.url, self.title, self.image_url, self.crop_areas]])

        form = self._init_form(csv_file, None)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {
            'batch_name': self.batch_name,
            'display_url': self.display_url,
            'brand_name': self.brand_name,
            'description': self.description,
            'call_to_action': self.call_to_action,
            'content_ads': [{
                u'crop_areas': self.crop_areas,
                u'image_url': self.image_url,
                u'title': self.title,
                u'url': self.url,
            }]
        })

    def test_incorrect_csv_format(self):
        csv_file = StringIO.StringIO()
        csv_file.write('TEST\x00TEST')

        form = self._init_form(csv_file, {'batch_name': self.batch_name})

        self.assertFalse(form.is_valid())

    def test_batch_name_missing(self):
        csv_file = self._get_csv_file(['Url', 'Title', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, {'batch_name': None})

        self.assertFalse(form.is_valid())

    def test_header_no_url(self):
        csv_file = self._get_csv_file(['aaa', 'Title', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['content_ads'], ['First column in header should be URL.'])

    def test_header_no_title(self):
        csv_file = self._get_csv_file(['URL', 'aaa', 'Image Url', 'Crop Areas'], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['content_ads'], ['Second column in header should be Title.'])

    def test_header_no_image_url(self):
        csv_file = self._get_csv_file(['URL', 'Title', 'aaa', 'Crop Areas'], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['content_ads'], ['Third column in header should be Image URL.'])

    def test_header_no_crop_areas(self):
        csv_file = self._get_csv_file(['URL', 'Title', 'Image URL', 'aaa'], [])
        form = self._init_form(csv_file, None)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['content_ads'], ['Fourth column in header should be Crop areas.'])

    def test_windows_1252_encoding(self):
        csv_file = self._get_csv_file(
            ['URL', 'Title', 'Image URL', 'Crop areas'],
            [[self.url, u'\u00ae', self.image_url, self.crop_areas]],
            encoding='windows-1252'
        )
        form = self._init_form(csv_file, None)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['content_ads'][0]['title'], u'\xae')

    def _init_form(self, csv_file, data_updates):
        data = {
            'batch_name': self.batch_name,
            'display_url': self.display_url,
            'brand_name': self.brand_name,
            'description': self.description,
            'call_to_action': self.call_to_action
        }

        if data_updates is not None:
            data.update(data_updates)

        return forms.AdGroupAdsPlusUploadForm(
            data,
            {'content_ads': SimpleUploadedFile('test_file.csv', csv_file.getvalue())}
        )

    def _get_csv_file(self, header, rows, encoding='utf-8'):
        csv_file = StringIO.StringIO()

        writer = unicodecsv.writer(csv_file, encoding=encoding)
        writer.writerow(header)

        for row in rows:
            writer.writerow(row)

        return csv_file
