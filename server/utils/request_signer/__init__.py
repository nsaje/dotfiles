'''
Sign https requests with hmac to ensure secrecy and security.
To ensure ssl certificate validity, use urllib2_secure_open.
'''

import urllib2
import httplib
import socket
import ssl
import os
import urlparse
import base64
import hmac
import hashlib
import time


TS_HEADER = 'Zapi-auth-ts'
SIGNATURE_HEADER = 'Zapi-auth-signature'

SIGNATURE_KEY_MIN_LEN = 16
MAX_TS_SKEW = 60 * 15  # disallow requests with clock skew of more than 15 minutes
CA_CERT_FILE = os.path.join(os.path.dirname(__file__), 'zemanta_ca_cert.pem')

LOCAL_HOSTS = ['localhost', '127.0.0.1']


class SignatureError(Exception):
    pass


def _validate_request(urllib_request):
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


def _get_signature(ts, path, query, data, secret_key):
    if data is None:
        data = ''

    request_content = '{}\n{}\n{}\n{}'.format(ts, path, query, data)
    signature = hmac.new(secret_key, request_content, hashlib.sha256)
    return base64.urlsafe_b64encode(signature.digest())


def sign_urllib2_request(urllib_request, secret_key):
    '''
    Adds signature to urllib2 request header.
    Only https post requests are supported.
    '''
    _validate_request(urllib_request)
    _validate_key(secret_key)

    parsed_selector = urlparse.urlparse(urllib_request.get_selector())

    ts = str(int(time.time()))
    signature = _get_signature(
        ts,
        parsed_selector.path,
        parsed_selector.query,
        urllib_request.get_data(),
        secret_key,
    )

    urllib_request.add_header(TS_HEADER, ts)
    urllib_request.add_header(SIGNATURE_HEADER, signature)


def get_wsgi_header_field_name(header):
    return 'HTTP_{}'.format(header.upper().replace('-', '_'))


def _normalize_signature(signature):
    # convert normal base64 to urlsafe base64
    return signature.replace('+', '-').replace('/', '_')


def verify_wsgi_request(wsgi_request, secret_keys):
    '''
    Verfies if header with signature matches calculated signature.
    Otherwise SignatureError is raised.
    '''
    header_signature = wsgi_request.META.get(
        get_wsgi_header_field_name(SIGNATURE_HEADER)
    )
    header_ts = wsgi_request.META.get(
        get_wsgi_header_field_name(TS_HEADER)
    )

    if not header_signature:
        raise SignatureError('Missing signature')

    ts_now = time.time()
    try:
        ts_seconds = int(header_ts)
    except:
        raise SignatureError('Invalid timestamp')
    if not ts_now - MAX_TS_SKEW < ts_seconds < ts_now + MAX_TS_SKEW:
        raise SignatureError('Request out of timestamp boundaries')

    header_signature = _normalize_signature(header_signature)

    if isinstance(secret_keys, basestring):
        secret_keys = [secret_keys]
    for secret_key in secret_keys:
        calc_signature = _get_signature(
            header_ts,
            wsgi_request.META.get('PATH_INFO'),
            wsgi_request.META.get('QUERY_STRING'),
            wsgi_request.body,
            secret_key,
        )

        if calc_signature == header_signature:
            return
    raise SignatureError('Invalid signature')


class _ValidHTTPSConnection(httplib.HTTPConnection):
    "This class allows communication via SSL."

    default_port = httplib.HTTPS_PORT

    def __init__(self, *args, **kwargs):
        httplib.HTTPConnection.__init__(self, *args, **kwargs)

    def connect(self):
        "Connect to a host on a given (SSL) port."

        sock = socket.create_connection(
            (self.host, self.port),
            self.timeout,
            self.source_address,
        )

        if self._tunnel_host:
            self.sock = sock
            self._tunnel()

        self.sock = ssl.wrap_socket(
            sock,
            cert_reqs=ssl.CERT_NONE,
        )


class _ValidHTTPSHandler(urllib2.HTTPSHandler):

    def https_open(self, req):
        return self.do_open(_ValidHTTPSConnection, req)


_secure_opener = urllib2.build_opener(_ValidHTTPSHandler)


def urllib2_secure_open(urllib_request, secret_key):
    '''
    Create secure connection with server certificate verification.
    '''
    sign_urllib2_request(urllib_request, secret_key)
    return _secure_opener.open(urllib_request)
