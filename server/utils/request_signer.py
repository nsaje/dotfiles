import urlparse
import base64
import hmac
import hashlib


SIGNATURE_HEADER = 'Zem-sign'
SIGNATURE_KEY_MIN_LEN = 16

LOCAL_HOSTS = ['localhost', '127.0.0.1']


class SignatureError(Exception):
    pass


def _validate_request(urllib_request):
    if urllib_request.get_method() != 'POST':
        raise SignatureError('Only POST requests are allowed')

    # Force https for requests outside of localhost
    if urllib_request.get_type() != 'https' and \
            urllib_request.get_origin_req_host() not in LOCAL_HOSTS:
        raise SignatureError('Only https requests are allowed for public hosts')


def _validate_key(secret_key):
    if not isinstance(secret_key, (str, unicode)):
        raise SignatureError('Invalid key type')

    if not secret_key:
        raise SignatureError('Empty key')

    if len(secret_key) < SIGNATURE_KEY_MIN_LEN:
        raise SignatureError(
            'Key too short, min length: {key_len}'.format(
                key_len=SIGNATURE_KEY_MIN_LEN,
            )
        )


def _get_signature(path, query, data, secret_key):
    request_content = '{}\n{}\n{}'.format(path, query, data)
    signature = hmac.new(secret_key, request_content, hashlib.sha256)
    return base64.urlsafe_b64encode(signature.digest())[:43]


def sign(urllib_request, secret_key):
    _validate_request(urllib_request)
    _validate_key(secret_key)

    parsed_selector = urlparse.urlparse(urllib_request.get_selector())

    signature = _get_signature(
        parsed_selector.path,
        parsed_selector.query,
        urllib_request.get_data(),
        secret_key,
    )

    urllib_request.add_header(SIGNATURE_HEADER, signature)


def _get_wsgi_header_field(header):
    return 'HTTP_{}'.format(header.upper().replace('-', '_'))


def verify(wsgi_request, secret_key):
    header_signature = wsgi_request.META.get(
        _get_wsgi_header_field(SIGNATURE_HEADER.upper())
    )
    if not header_signature:
        raise SignatureError('Missing signature')

    calc_signature = _get_signature(
        wsgi_request.META.get('PATH_INFO'),
        wsgi_request.META.get('QUERY_STRING'),
        wsgi_request.body,
        secret_key,
    )

    if calc_signature != header_signature:
        raise SignatureError('Invalid signature')
