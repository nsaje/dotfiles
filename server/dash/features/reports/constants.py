import stats.constants
import utils.columns
from utils.constant_base import ConstantBase

EQUALS = "="
IN = "IN"
BETWEEN = "between"
OPERATORS = [EQUALS, IN, BETWEEN]

BREAKDOWN_FIELDS = set(
    stats.constants.StructureDimension._ALL
    + stats.constants.TimeDimension._ALL
    + stats.constants.DeliveryDimension._ALL
)

HIERARCHY_BREAKDOWN_FIELDS = [
    stats.constants.ACCOUNT,
    stats.constants.CAMPAIGN,
    stats.constants.AD_GROUP,
    stats.constants.CONTENT_AD,
]

STRUCTURE_CONSTRAINTS_FIELDS = ["account_id", "campaign_id", "ad_group_id", "content_ad_id"]

MAX_ROWS = 999999

DEFAULT_ORDER = "-e_media_cost"

DATED_COLUMNS = (
    utils.columns.FieldNames.status,
    utils.columns.FieldNames.account_status,
    utils.columns.FieldNames.campaign_status,
    utils.columns.FieldNames.ad_group_status,
    utils.columns.FieldNames.content_ad_status,
    utils.columns.FieldNames.source_status,
    utils.columns.FieldNames.publisher_status,
)


class ReportJobStatus(ConstantBase):
    DONE = 1
    FAILED = 2
    IN_PROGRESS = 3
    CANCELLED = 4

    _VALUES = {DONE: "Done", FAILED: "Failed", IN_PROGRESS: "In progress", CANCELLED: "Cancelled"}
