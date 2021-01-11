import base64
import urllib.error
import urllib.parse
import urllib.request

import zstandard as zstd
from Crypto.Cipher import Blowfish
from django.conf import settings

from utils import zlogging

from . import redirectdata_pb2

logger = zlogging.getLogger(__name__)

REDIRECT_URL_TEMPLATE = (
    "{protocol}://r1-usc1.zemanta.com/rp2/{sourceDomain}/{ad_group_id}/{content_ad_id}/{enc_protobuf_data}/"
)
REDIRECT_URL_WITH_QUERY_PARAMS_TEMPLATE = "{protocol}://r1-usc1.zemanta.com/rp2/{sourceDomain}/{ad_group_id}/{content_ad_id}/{enc_protobuf_data}/?{query_params}"
SOURCE_Z1 = "z1"


def construct_redirector_url(
    ad_group_id,
    content_ad_id,
    campaign_id,
    account_id,
    landing_page_url="",
    url_params=None,
    protobuf_params=None,
    use_https=False,
    ga_tracking_enabled=False,
    adobe_tracking_enabled=False,
    tracking_codes="",
    adobe_tracking_param="",
):
    url_params_seq = list((url_params or {}).items())
    # handle AdTags
    if landing_page_url == "":
        url_params_seq.append(("rurl", ""))
    encoded_params = urllib.parse.urlencode(url_params_seq)

    redirect_data = redirectdata_pb2.RedirectData()
    redirect_data.campaign_id = int(campaign_id)
    redirect_data.account_id = int(account_id)
    redirect_data.redirect_url = landing_page_url
    redirect_data.ga_tracking_enabled = ga_tracking_enabled
    redirect_data.adobe_tracking_enabled = adobe_tracking_enabled
    redirect_data.tracking_codes = tracking_codes
    redirect_data.adobe_tracking_param = adobe_tracking_param

    for key, value in list((protobuf_params or {}).items()):
        if hasattr(redirect_data, key):
            setattr(redirect_data, key, value)
        else:
            raise Exception("Unsupported key: " + key + "(" + value + ")")

    enc_protobuf_data = compress_and_encrypt_params(redirect_data.SerializeToString())

    url_template = REDIRECT_URL_WITH_QUERY_PARAMS_TEMPLATE if len(url_params_seq) > 0 else REDIRECT_URL_TEMPLATE
    redirect_url = url_template.format(
        protocol="https" if use_https else "http",
        sourceDomain=SOURCE_Z1,
        ad_group_id=ad_group_id,
        content_ad_id=content_ad_id,
        enc_protobuf_data=enc_protobuf_data,
        query_params=encoded_params,
    )
    return redirect_url


def compress_and_encrypt_params(params):
    if not params:
        return ""

    zstd_compressor = zstd.ZstdCompressor(write_checksum=True, write_content_size=False)
    compressed_data = zstd_compressor.compress(params)

    modulus = len(compressed_data) % Blowfish.block_size
    pad_len = Blowfish.block_size - modulus
    for i in range(pad_len):
        compressed_data += bytes([pad_len])

    cipher = Blowfish.new(settings.R1_URL_PARAMS_ENCRYPTION_KEY, Blowfish.MODE_ECB)
    encrypted_data = cipher.encrypt(compressed_data)

    return base64.b32encode(encrypted_data).decode("utf-8").rstrip("=")
