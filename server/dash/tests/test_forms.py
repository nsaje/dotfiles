import unicodecsv
import StringIO

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

from dash.forms import AdGroupAdsPlusUploadForm


class AdGroupAdsPlusUploadFormTest(TestCase):
    def setUp(self):
        self.batch_name = 'Test batch name'
        self.url = 'http://example.com'
        self.title = 'Test Title'
        self.image_url = 'http://example.com/image'
        self.crop_areas = '(((44, 22), (144, 122)), ((33, 22), (177, 122)))'

    def test_form(self):
        csv_file = self._get_csv_file(
            [[self.url, self.title, self.image_url, self.crop_areas]])

        form = self._init_form(csv_file, self.batch_name)

        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data, {
            'batch_name': self.batch_name,
            'content_ads': [{
                u'crop_areas': [[[44, 22], [144, 122]], [[33, 22], [177, 122]]],
                u'image_url': self.image_url,
                u'title': self.title,
                u'url': self.url
            }]
        })

    def test_incorrect_csv_format(self):
        csv_file = StringIO.StringIO()
        csv_file.write('TEST\x00TEST')

        form = self._init_form(csv_file, self.batch_name)

        self.assertFalse(form.is_valid())

    def test_no_url(self):
        csv_file = self._get_csv_file([[None, self.title, self.image_url, self.crop_areas]])
        form = self._init_form(csv_file, self.batch_name)

        self.assertFalse(form.is_valid())

    def test_no_title(self):
        csv_file = self._get_csv_file([[self.url, None, self.image_url, self.crop_areas]])
        form = self._init_form(csv_file, self.batch_name)

        self.assertFalse(form.is_valid())

    def test_crop_areas_wrong_format(self):
        crop_areas = '(((44), (144, 122)), ((33, 22), (177, 122)))'

        csv_file = self._get_csv_file([[self.url, self.title, self.image_url, crop_areas]])
        form = self._init_form(csv_file, self.batch_name)

        self.assertFalse(form.is_valid())

    def test_crop_areas_missing(self):
        csv_file = self._get_csv_file([[self.url, self.title, self.image_url, None]])
        form = self._init_form(csv_file, self.batch_name)

        self.assertTrue(form.is_valid())

    def test_batch_name_missing(self):
        csv_file = self._get_csv_file([])
        form = self._init_form(csv_file, None)

        self.assertFalse(form.is_valid())

    def _init_form(self, csv_file, batch_name):
        return AdGroupAdsPlusUploadForm(
            {'batch_name': batch_name},
            {'content_ads': SimpleUploadedFile('test_file.csv', csv_file.getvalue())}
        )

    def _get_csv_file(self, rows):
        csv_file = StringIO.StringIO()

        writer = unicodecsv.writer(csv_file)
        writer.writerow(['Url', 'Title', 'Image Url', 'Crop Areas'])

        for row in rows:
            writer.writerow(row)

        return csv_file
