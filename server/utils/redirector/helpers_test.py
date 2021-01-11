import urllib.parse

from django.test import TestCase

from . import helpers
from . import redirectdata_pb2


class ConstructRedirectorURLTestCase(TestCase):
    maxDiff = None

    def test_construct_redirector_url(self):
        redirect_data = redirectdata_pb2.RedirectData()
        redirect_data.campaign_id = 3
        redirect_data.account_id = 4

        redirect_data.redirect_url = "http://localhost:8000"
        encrypted_data = helpers.compress_and_encrypt_params(redirect_data.SerializeToString())
        result = helpers.construct_redirector_url("1", "2", "3", "4", redirect_data.redirect_url)
        expected = "http://r1-usc1.zemanta.com/rp2/" + helpers.SOURCE_Z1 + "/1/2/" + encrypted_data + "/"
        self.assertEqual(result, expected)

        redirect_data.redirect_url = "http://localhost:8000?test={macro}&test=with space"
        encrypted_data = helpers.compress_and_encrypt_params(redirect_data.SerializeToString())
        result = helpers.construct_redirector_url("1", "2", "3", "4", redirect_data.redirect_url)
        expected = "http://r1-usc1.zemanta.com/rp2/" + helpers.SOURCE_Z1 + "/1/2/" + encrypted_data + "/"
        self.assertEqual(result, expected)

        redirect_data.redirect_url = "http://localhost:8000"
        encrypted_data = helpers.compress_and_encrypt_params(redirect_data.SerializeToString())
        result = helpers.construct_redirector_url(
            "1", "2", "3", "4", redirect_data.redirect_url, url_params={"key1": "val1"}
        )
        expected = "http://r1-usc1.zemanta.com/rp2/" + helpers.SOURCE_Z1 + "/1/2/" + encrypted_data + "/?key1=val1"
        self.assertEqual(result, expected)

    def test_construct_redirector_url_encrypted_content(self):
        result = helpers.construct_redirector_url("1", "2", "3", "4", "http://localhost:8000")
        expected = (
            "http://r1-usc1.zemanta.com/rp2/"
            + helpers.SOURCE_Z1
            + "/1/2/SVNB33U7NNUFZSRPQRD4J7VEHPMHDSJE27JLSPLF23EBARCFZ6FSOWIMG6SOJXASYJKUQ67ZTNVZ6/"
        )
        self.assertEqual(result, expected)

    def test_construct_redirector_url_adtags(self):
        redirect_data = redirectdata_pb2.RedirectData()
        redirect_data.campaign_id = 3
        redirect_data.account_id = 4
        encrypted_data = helpers.compress_and_encrypt_params(redirect_data.SerializeToString())

        result = helpers.construct_redirector_url("1", "2", "3", "4")
        expected = "http://r1-usc1.zemanta.com/rp2/" + helpers.SOURCE_Z1 + "/1/2/" + encrypted_data + "/?rurl="
        self.assertEqual(result, expected)

    def test_construct_redirector_url_protobbuf_params(self):
        redirect_data = redirectdata_pb2.RedirectData()
        redirect_data.campaign_id = 3
        redirect_data.account_id = 4
        redirect_data.redirect_url = "http://localhost:8000"
        redirect_data.publisher_domain = "publisher.domain.com"
        encrypted_data = helpers.compress_and_encrypt_params(redirect_data.SerializeToString())

        result = helpers.construct_redirector_url(
            "1",
            "2",
            "3",
            "4",
            redirect_data.redirect_url,
            protobuf_params={"publisher_domain": redirect_data.publisher_domain},
        )
        expected = "http://r1-usc1.zemanta.com/rp2/" + helpers.SOURCE_Z1 + "/1/2/" + encrypted_data + "/"
        self.assertEqual(result, expected)

        result = helpers.construct_redirector_url(
            "1",
            "2",
            "3",
            "4",
            redirect_data.redirect_url,
            protobuf_params={"publisher_domain": redirect_data.publisher_domain},
            url_params={"key1": "val1"},
        )
        expected = "http://r1-usc1.zemanta.com/rp2/" + helpers.SOURCE_Z1 + "/1/2/" + encrypted_data + "/?key1=val1"
        self.assertEqual(result, expected)

        with self.assertRaises(Exception):
            helpers.construct_redirector_url(
                "1",
                "2",
                "3",
                "4",
                redirect_data.redirect_url,
                protobuf_params={"non_existent_field": "it should return an exception"},
            )

    def test_construct_redirector_url_for_outbrain(self):
        redirect_data = redirectdata_pb2.RedirectData()
        redirect_data.campaign_id = 3
        redirect_data.account_id = 4
        redirect_data.redirect_url = "http://localhost:8000"
        encrypted_data = helpers.compress_and_encrypt_params(redirect_data.SerializeToString())

        result = helpers.construct_redirector_url(
            "1", "2", "3", "4", redirect_data.redirect_url, url_params={"_r_outbrainpubid": "${PUBID}"}
        )
        expected = (
            "http://r1-usc1.zemanta.com/rp2/"
            + helpers.SOURCE_Z1
            + "/1/2/"
            + encrypted_data
            + "/?_r_outbrainpubid=%24%7BPUBID%7D"
        )
        self.assertEqual(result, expected)


class CompressAndEncryptParamsTestCase(TestCase):
    maxDiff = None

    def test_compress_and_encrypt_params(self):
        params_dict = {"aid": 123, "caid": 321, "rurl": "http://test.com"}
        params = urllib.parse.urlencode(params_dict)
        result = helpers.compress_and_encrypt_params(str.encode(params))
        self.assertEqual(
            "KUDY2RGA4TZS2DO33PUCPSA4KZHCTHCOEXATZ6N7LAKIPCBPDFVSGIKKUCCD3NSXTUIJFR6IQ6FIIB257ZZMU45A7PEN5CF4OPIPE6I",
            result,
        )
