import base64
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.parse
import urllib.request

SECRET = "a" * 16
ZEMANTA_ENDPOINT = "http://localhost:8000/integrations/businesswire/promotion_export/"
BIZWIRE_URL = (
    "http://www.businesswire.com/news/home/20160817005626/en/Global-78-kda-Glucose-Regulated-Protein-Pipeline-Review"
)
TS_HEADER = "Zapi-auth-ts"
SIGNATURE_HEADER = "Zapi-auth-signature"


encoded_query = urllib.parse.urlencode({"article_url": BIZWIRE_URL})

request_url = "{}?{}".format(ZEMANTA_ENDPOINT, encoded_query)

urllib_request = urllib.request.Request(url=request_url)

parsed_selector = urllib.parse.urlparse(urllib_request.get_selector())


ts = str(int(time.time()))
request_content = "{}\n{}\n{}\n{}".format(ts, parsed_selector.path, parsed_selector.query, "")
signature = hmac.new(SECRET, request_content, hashlib.sha256)
signature_base64 = base64.urlsafe_b64encode(signature.digest())


urllib_request.add_header(TS_HEADER, ts)
urllib_request.add_header(SIGNATURE_HEADER, signature_base64)

response = urllib.request.urlopen(urllib_request)

assert response.getcode() == 200

json_data = json.load(response)

print(json_data)
