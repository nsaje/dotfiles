from django.conf import settings
from django.db import transaction

import core.models
import dash.constants
import utils.k1_helper
import utils.progress_bar
from utils import zlogging
from utils.command_helpers import Z1Command

logger = zlogging.getLogger(__name__)


EXCLUDE_BROWSERS_AD_GROUPS = {609725: [dash.constants.BrowserFamily.SAFARI]}

EXCLUDE_BROWSERS_CAMPAIGNS = {
    1064546: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1268813: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1472652: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1472651: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1583161: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1472657: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1419042: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1268811: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1472659: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1472658: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1583162: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1472662: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1472655: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1472654: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1529098: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1472653: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1472650: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1620649: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    1620648: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    1620651: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    1620650: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    1419068: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE],
    1268831: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE],
    1064407: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE],
    1419067: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE],
    1582642: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE],
    1582677: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE],
    1801524: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1801522: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1801671: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1801612: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1804802: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1804773: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1614849: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1614850: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    1801595: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    1801587: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    1801711: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    1801739: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    1804803: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    1804797: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    1993229: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2056371: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2056519: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119422: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119566: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119591: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119597: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119599: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119601: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119604: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119606: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119607: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119608: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2119609: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2181932: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2181933: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2181921: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2181913: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2196869: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2197060: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2181885: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2181882: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2212525: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2208072: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2250576: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2250468: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2361969: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2361991: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2362126: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2362164: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2362218: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2363443: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2519880: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2519883: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2519889: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2566214: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2566353: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2566538: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2566540: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2566340: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2566354: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2566427: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2566499: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2566367: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2566370: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2623435: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2623561: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2623655: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2623661: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2623680: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2623805: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2624059: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    2624126: [
        dash.constants.BrowserFamily.IE,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
}

EXCLUDE_BROWSERS_ACCOUNTS = {
    3743: [dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    4500: [dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    4131: [dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    4224: [dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    4133: [dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    4273: [],
    5960: [dash.constants.BrowserFamily.FIREFOX],
    6275: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6276: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6277: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    5666: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    6005: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.FIREFOX,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    5677: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAMSUNG,
        dash.constants.BrowserFamily.FIREFOX,
    ],
    6538: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    5364: [dash.constants.BrowserFamily.IE, dash.constants.BrowserFamily.FIREFOX],
    6598: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6674: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX, dash.constants.BrowserFamily.IE],
    6597: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6604: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6595: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6596: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6636: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6610: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6652: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6692: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    6325: [dash.constants.BrowserFamily.FIREFOX],
    6441: [dash.constants.BrowserFamily.FIREFOX],
    6696: [dash.constants.BrowserFamily.FIREFOX],
    6695: [dash.constants.BrowserFamily.FIREFOX],
    6675: [dash.constants.BrowserFamily.FIREFOX],
    6457: [dash.constants.BrowserFamily.FIREFOX],
    6413: [dash.constants.BrowserFamily.FIREFOX],
    5387: [dash.constants.BrowserFamily.IE],
    5729: [dash.constants.BrowserFamily.IE],
    5739: [dash.constants.BrowserFamily.IE],
    5740: [dash.constants.BrowserFamily.IE],
    5741: [dash.constants.BrowserFamily.IE],
    6024: [dash.constants.BrowserFamily.IE],
    6025: [dash.constants.BrowserFamily.IE],
    6026: [dash.constants.BrowserFamily.IE],
    6655: [dash.constants.BrowserFamily.IE],
    7216: [dash.constants.BrowserFamily.FIREFOX, dash.constants.BrowserFamily.SAFARI],
}

EXCLUDE_BROWSERS_AGENCIES = {448: [dash.constants.BrowserFamily.IE]}

INCLUDED_BROWSERS_AD_GROUPS = {
    1369958: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370031: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370060: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370701: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370705: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370772: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370831: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370836: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370929: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370945: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370951: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1370952: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1371088: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1371146: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1383955: [dash.constants.BrowserFamily.CHROME],
    1417327: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1417396: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1417398: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1417430: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1417432: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1417461: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1410101: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1410275: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1410276: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1410620: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1410621: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1410623: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1410922: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1410931: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1410939: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1452698: [dash.constants.BrowserFamily.IE],
    2594010: [dash.constants.BrowserFamily.CHROME],
}

INCLUDED_BROWSERS_CAMPAIGNS = {
    926238: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    926244: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    926243: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    926240: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    926241: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    927068: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    927036: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    874948: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    874949: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    874918: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    843675: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    848733: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    843652: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    875351: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    920525: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.FIREFOX],
    920053: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.FIREFOX],
    935385: [dash.constants.BrowserFamily.CHROME],
    849386: [dash.constants.BrowserFamily.CHROME],
    935088: [dash.constants.BrowserFamily.CHROME],
    935438: [dash.constants.BrowserFamily.CHROME],
    849387: [dash.constants.BrowserFamily.CHROME],
    849389: [dash.constants.BrowserFamily.CHROME],
    940504: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    940570: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    940573: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    940578: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    940531: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    942436: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    940989: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    940998: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    954438: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    1185360: [dash.constants.BrowserFamily.EDGE],
    1185371: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.SAFARI,
        dash.constants.BrowserFamily.IE,
    ],
    1620806: [dash.constants.BrowserFamily.EDGE],
    1620805: [dash.constants.BrowserFamily.EDGE],
    2119594: [dash.constants.BrowserFamily.EDGE],
    2119603: [dash.constants.BrowserFamily.EDGE],
    2181934: [dash.constants.BrowserFamily.EDGE],
    2181935: [dash.constants.BrowserFamily.EDGE],
    2255726: [dash.constants.BrowserFamily.EDGE],
    2255727: [dash.constants.BrowserFamily.EDGE],
    2258847: [dash.constants.BrowserFamily.EDGE],
    2258851: [dash.constants.BrowserFamily.EDGE],
    2257646: [dash.constants.BrowserFamily.EDGE],
    2257895: [dash.constants.BrowserFamily.EDGE],
    2258235: [dash.constants.BrowserFamily.EDGE],
    2258266: [dash.constants.BrowserFamily.EDGE],
    2279466: [dash.constants.BrowserFamily.CHROME],
    1761122: [dash.constants.BrowserFamily.CHROME],
    2113724: [dash.constants.BrowserFamily.CHROME],
    2362207: [dash.constants.BrowserFamily.EDGE],
    2362229: [dash.constants.BrowserFamily.EDGE],
    2362486: [dash.constants.BrowserFamily.EDGE],
    2362979: [dash.constants.BrowserFamily.EDGE],
    2566355: [dash.constants.BrowserFamily.EDGE],
    2566358: [dash.constants.BrowserFamily.EDGE],
    2566541: [dash.constants.BrowserFamily.EDGE],
    2566542: [dash.constants.BrowserFamily.EDGE],
    2566368: [dash.constants.BrowserFamily.EDGE],
    2566371: [dash.constants.BrowserFamily.EDGE],
    2566404: [dash.constants.BrowserFamily.EDGE],
    2566409: [dash.constants.BrowserFamily.EDGE],
    2623891: [dash.constants.BrowserFamily.EDGE],
    2623577: [dash.constants.BrowserFamily.EDGE],
    2623596: [dash.constants.BrowserFamily.EDGE],
    2624310: [dash.constants.BrowserFamily.EDGE],
    2624372: [dash.constants.BrowserFamily.EDGE],
}

INCLUDED_BROWSERS_ACCOUNTS = {
    5709: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    5748: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    5746: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    5739: [dash.constants.BrowserFamily.CHROME],
    5740: [dash.constants.BrowserFamily.CHROME],
    5741: [dash.constants.BrowserFamily.SAFARI, dash.constants.BrowserFamily.FIREFOX],
    5742: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    5829: [dash.constants.BrowserFamily.EDGE],
    5793: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    5887: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    5886: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    5959: [dash.constants.BrowserFamily.SAFARI],
    5958: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.IE],
    5957: [dash.constants.BrowserFamily.EDGE],
    6024: [dash.constants.BrowserFamily.CHROME],
    6025: [dash.constants.BrowserFamily.CHROME],
    6026: [dash.constants.BrowserFamily.CHROME],
    6045: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    5809: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    6075: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    6112: [dash.constants.BrowserFamily.CHROME],
    5429: [
        dash.constants.BrowserFamily.CHROME,
        dash.constants.BrowserFamily.EDGE,
        dash.constants.BrowserFamily.SAMSUNG,
    ],
    6351: [dash.constants.BrowserFamily.EDGE],
    5696: [dash.constants.BrowserFamily.CHROME],
    6511: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.CHROME],
    6513: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.CHROME],
    6550: [dash.constants.BrowserFamily.CHROME],
    6619: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.CHROME],
    6613: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.CHROME],
    6621: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.CHROME],
    6615: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.CHROME],
    6617: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.CHROME],
    6626: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.CHROME],
    6628: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.CHROME],
    6630: [dash.constants.BrowserFamily.EDGE, dash.constants.BrowserFamily.CHROME],
    6649: [dash.constants.BrowserFamily.CHROME],
    6659: [dash.constants.BrowserFamily.CHROME],
    6660: [dash.constants.BrowserFamily.CHROME],
    6655: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    6753: [dash.constants.BrowserFamily.CHROME],
    6766: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.EDGE],
    6780: [dash.constants.BrowserFamily.CHROME],
    6781: [dash.constants.BrowserFamily.CHROME],
    6783: [dash.constants.BrowserFamily.CHROME],
    6784: [dash.constants.BrowserFamily.CHROME],
    6546: [dash.constants.BrowserFamily.CHROME],
    6275: [dash.constants.BrowserFamily.CHROME],
    6276: [dash.constants.BrowserFamily.CHROME],
    6277: [dash.constants.BrowserFamily.CHROME],
    6545: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.SAFARI],
    6902: [dash.constants.BrowserFamily.CHROME],
    6903: [dash.constants.BrowserFamily.CHROME],
    6879: [dash.constants.BrowserFamily.CHROME],
    6880: [dash.constants.BrowserFamily.CHROME],
    6881: [dash.constants.BrowserFamily.CHROME],
    6790: [dash.constants.BrowserFamily.CHROME],
    6925: [dash.constants.BrowserFamily.EDGE],
    7051: [dash.constants.BrowserFamily.CHROME],
    7052: [dash.constants.BrowserFamily.CHROME],
    7053: [dash.constants.BrowserFamily.CHROME],
    7054: [dash.constants.BrowserFamily.CHROME],
    7349: [dash.constants.BrowserFamily.CHROME],
    7348: [dash.constants.BrowserFamily.CHROME],
    7347: [dash.constants.BrowserFamily.CHROME],
    7346: [dash.constants.BrowserFamily.CHROME],
    7345: [dash.constants.BrowserFamily.CHROME],
    7344: [dash.constants.BrowserFamily.CHROME],
    7343: [dash.constants.BrowserFamily.CHROME],
    7342: [dash.constants.BrowserFamily.CHROME],
    7339: [dash.constants.BrowserFamily.CHROME],
    7489: [dash.constants.BrowserFamily.CHROME],
    7490: [dash.constants.BrowserFamily.CHROME],
    7142: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.SAFARI],
    7241: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.SAFARI],
    7375: [dash.constants.BrowserFamily.CHROME, dash.constants.BrowserFamily.SAFARI],
}


class Command(Z1Command):
    help = "Apply B1 browsers targeting hacks to ad groups."

    def add_arguments(self, parser):
        parser.add_argument("--revert", action="store_true", help="Revert B1 browsers targeting hacks")

    def handle(self, *args, **options):
        """
        Temporary management command to migrate B1 browsers targeting hacks to
        Z1 ad groups. Will be removed after migration is done.
        """

        revert = options.get("revert")
        if revert:
            logger.info("Star reverting B1 browsers targeting hacks on ad groups...")
            self._revert_browsers_targeting()
            logger.info("Reverting B1 browsers targeting hacks on ad groups completed...")
        else:
            logger.info("Star applying B1 browsers targeting hacks to ad groups...")
            self._apply_browsers_targeting()
            logger.info("Applying B1 browsers targeting hacks to ad groups completed...")

    def _apply_browsers_targeting(self):
        count = len(EXCLUDE_BROWSERS_AD_GROUPS.items())
        if count > 0:
            with transaction.atomic():
                logger.info("Start handling EXCLUDE_BROWSERS_AD_GROUPS...", count=count)
                utils.progress_bar.print_progress_bar(0, count)
                for index, (key, value) in enumerate(EXCLUDE_BROWSERS_AD_GROUPS.items()):
                    qs = core.models.AdGroup.objects.filter(pk=key).exclude_archived()
                    self._handle_excluded_browsers_targeting(qs, value)
                    utils.progress_bar.print_progress_bar(index + 1, count)
                logger.info("Finish handling EXCLUDE_BROWSERS_AD_GROUPS...", count=count)

        count = len(EXCLUDE_BROWSERS_CAMPAIGNS.items())
        if count > 0:
            with transaction.atomic():
                logger.info("Start handling EXCLUDE_BROWSERS_CAMPAIGNS...", count=count)
                utils.progress_bar.print_progress_bar(0, count)
                for index, (key, value) in enumerate(EXCLUDE_BROWSERS_CAMPAIGNS.items()):
                    qs = core.models.AdGroup.objects.filter(campaign_id=key).exclude_archived()
                    self._handle_excluded_browsers_targeting(qs, value)
                    utils.progress_bar.print_progress_bar(index + 1, count)
                logger.info("Finish handling EXCLUDE_BROWSERS_CAMPAIGNS...", count=count)

        count = len(EXCLUDE_BROWSERS_ACCOUNTS.items())
        if count > 0:
            with transaction.atomic():
                logger.info("Start handling EXCLUDE_BROWSERS_ACCOUNTS...", count=count)
                utils.progress_bar.print_progress_bar(0, count)
                for index, (key, value) in enumerate(EXCLUDE_BROWSERS_ACCOUNTS.items()):
                    qs = core.models.AdGroup.objects.filter(campaign__account_id=key).exclude_archived()
                    self._handle_excluded_browsers_targeting(qs, value)
                    utils.progress_bar.print_progress_bar(index + 1, count)
                logger.info("Finish handling EXCLUDE_BROWSERS_ACCOUNTS...", count=count)

        count = len(EXCLUDE_BROWSERS_AGENCIES.items())
        if count > 0:
            with transaction.atomic():
                logger.info("Start handling EXCLUDE_BROWSERS_AGENCIES...", count=count)
                utils.progress_bar.print_progress_bar(0, count)
                for index, (key, value) in enumerate(EXCLUDE_BROWSERS_AGENCIES.items()):
                    qs = core.models.AdGroup.objects.filter(campaign__account__agency_id=key).exclude_archived()
                    self._handle_excluded_browsers_targeting(qs, value)
                    utils.progress_bar.print_progress_bar(index + 1, count)
                logger.info("Finish handling EXCLUDE_BROWSERS_AGENCIES...", count=count)

        count = len(INCLUDED_BROWSERS_AD_GROUPS.items())
        if count > 0:
            with transaction.atomic():
                logger.info("Start handling INCLUDED_BROWSERS_AD_GROUPS...", count=count)
                utils.progress_bar.print_progress_bar(0, count)
                for index, (key, value) in enumerate(INCLUDED_BROWSERS_AD_GROUPS.items()):
                    qs = core.models.AdGroup.objects.filter(pk=key).exclude_archived()
                    self._handle_included_browsers_targeting(qs, value)
                    utils.progress_bar.print_progress_bar(index + 1, count)
                logger.info("Finish handling INCLUDED_BROWSERS_AD_GROUPS...", count=count)

        count = len(INCLUDED_BROWSERS_CAMPAIGNS.items())
        if count > 0:
            with transaction.atomic():
                logger.info("Start handling INCLUDED_BROWSERS_CAMPAIGNS...", count=count)
                utils.progress_bar.print_progress_bar(0, count)
                for index, (key, value) in enumerate(INCLUDED_BROWSERS_CAMPAIGNS.items()):
                    qs = core.models.AdGroup.objects.filter(campaign_id=key).exclude_archived()
                    self._handle_included_browsers_targeting(qs, value)
                    utils.progress_bar.print_progress_bar(index + 1, count)
                logger.info("Finish handling INCLUDED_BROWSERS_CAMPAIGNS...", count=count)

        count = len(INCLUDED_BROWSERS_ACCOUNTS.items())
        if count > 0:
            with transaction.atomic():
                logger.info("Start handling INCLUDED_BROWSERS_ACCOUNTS...", count=count)
                utils.progress_bar.print_progress_bar(0, count)
                for index, (key, value) in enumerate(INCLUDED_BROWSERS_ACCOUNTS.items()):
                    qs = core.models.AdGroup.objects.filter(campaign__account_id=key).exclude_archived()
                    self._handle_included_browsers_targeting(qs, value)
                    utils.progress_bar.print_progress_bar(index + 1, count)
                logger.info("Finish handling INCLUDED_BROWSERS_ACCOUNTS...", count=count)

    def _revert_browsers_targeting(self):
        logger.info("Start reverting EXCLUDE_BROWSERS_AD_GROUPS...")
        qs = core.models.AdGroup.objects.filter(id__in=list(EXCLUDE_BROWSERS_AD_GROUPS.keys())).exclude_archived()
        self._handle_reset_browsers_targeting(qs)
        logger.info("Finish reverting EXCLUDE_BROWSERS_AD_GROUPS...")

        logger.info("Start reverting EXCLUDE_BROWSERS_CAMPAIGNS...")
        qs = core.models.AdGroup.objects.filter(
            campaign_id__in=list(EXCLUDE_BROWSERS_CAMPAIGNS.keys())
        ).exclude_archived()
        self._handle_reset_browsers_targeting(qs)
        logger.info("Finish reverting EXCLUDE_BROWSERS_CAMPAIGNS...")

        logger.info("Start reverting EXCLUDE_BROWSERS_ACCOUNTS...")
        qs = core.models.AdGroup.objects.filter(
            campaign__account_id__in=list(EXCLUDE_BROWSERS_ACCOUNTS.keys())
        ).exclude_archived()
        self._handle_reset_browsers_targeting(qs)
        logger.info("Finish reverting EXCLUDE_BROWSERS_ACCOUNTS...")

        logger.info("Start reverting EXCLUDE_BROWSERS_AGENCIES...")
        qs = core.models.AdGroup.objects.filter(
            campaign__account__agency_id__in=list(EXCLUDE_BROWSERS_AGENCIES.keys())
        ).exclude_archived()
        self._handle_reset_browsers_targeting(qs)
        logger.info("Finish reverting EXCLUDE_BROWSERS_AGENCIES...")

        logger.info("Start reverting INCLUDED_BROWSERS_AD_GROUPS...")
        qs = core.models.AdGroup.objects.filter(pk__in=list(INCLUDED_BROWSERS_AD_GROUPS.keys())).exclude_archived()
        self._handle_reset_browsers_targeting(qs)
        logger.info("Finish reverting INCLUDED_BROWSERS_AD_GROUPS...")

        logger.info("Start reverting INCLUDED_BROWSERS_CAMPAIGNS...")
        qs = core.models.AdGroup.objects.filter(
            campaign_id__in=list(INCLUDED_BROWSERS_CAMPAIGNS.keys())
        ).exclude_archived()
        self._handle_reset_browsers_targeting(qs)
        logger.info("Finish reverting INCLUDED_BROWSERS_CAMPAIGNS...")

        logger.info("Start reverting INCLUDED_BROWSERS_ACCOUNTS...")
        qs = core.models.AdGroup.objects.filter(
            campaign__account_id__in=list(INCLUDED_BROWSERS_ACCOUNTS.keys())
        ).exclude_archived()
        self._handle_reset_browsers_targeting(qs)
        logger.info("Finish reverting INCLUDED_BROWSERS_ACCOUNTS...")

    @staticmethod
    def _handle_included_browsers_targeting(ad_group_qs, browsers):
        for ad_group in ad_group_qs:
            target_browsers = ad_group.settings.target_browsers or []
            if len(target_browsers) > 0:
                continue
            exclusion_target_browsers = ad_group.settings.exclusion_target_browsers or []
            if len(exclusion_target_browsers) > 0:
                continue
            for browser in browsers:
                target_browsers.append({"family": browser})
            ad_group.settings.update(None, target_browsers=target_browsers, exclusion_target_browsers=None)

    @staticmethod
    def _handle_excluded_browsers_targeting(ad_group_qs, browsers):
        for ad_group in ad_group_qs:
            target_browsers = ad_group.settings.target_browsers or []
            if len(target_browsers) > 0:
                continue
            exclusion_target_browsers = ad_group.settings.exclusion_target_browsers or []
            if len(exclusion_target_browsers) > 0:
                continue
            for browser in browsers:
                exclusion_target_browsers.append({"family": browser})
            ad_group.settings.update(None, target_browsers=None, exclusion_target_browsers=exclusion_target_browsers)

    def _handle_reset_browsers_targeting(self, ad_group_qs):
        count = ad_group_qs.count()
        if count == 0:
            return
        utils.progress_bar.print_progress_bar(0, count)
        for index, ad_group in enumerate(ad_group_qs):
            target_browsers = ad_group.settings.target_browsers or []
            exclusion_target_browsers = ad_group.settings.exclusion_target_browsers or []
            if len(target_browsers) > 0 or len(exclusion_target_browsers) > 0:
                ad_group.settings.update(None, target_browsers=None, exclusion_target_browsers=None)
                utils.k1_helper.update_ad_group(ad_group, priority=True)
            utils.progress_bar.print_progress_bar(index + 1, count)
