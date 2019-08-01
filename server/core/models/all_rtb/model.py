from decimal import Decimal

from core.models.ad_group_source import AdGroupSource
from core.models.source import Source
from core.models.source_type import SourceType

AllRTBSourceType = SourceType(
    id="source-type-0123456789",
    type="all-rtb",
    min_cpc=Decimal("0.01"),
    min_cpm=Decimal("0.01"),
    min_daily_budget=Decimal("1.00"),
    max_cpc=Decimal("20.0"),
    max_cpm=Decimal("25.0"),
    max_daily_budget=Decimal("10000.00"),
    cpc_decimal_places=4,
)

AllRTBSource = Source(
    id="0123456789",
    name="RTB Sources",
    maintenance=False,
    source_type=AllRTBSourceType,
    default_daily_budget_cc=Decimal("50.00"),
    default_cpc_cc=Decimal("0.4500"),
    default_cpm=Decimal("1.0000"),
)


class AllRTBAdGroupSource(AdGroupSource):
    class Meta:
        app_label = "dash"
        proxy = True

    def __init__(self, ad_group):
        super().__init__()
        self.id = "0123456789-%s" % ad_group.id
        self.ad_group = ad_group
        self.source = AllRTBSource
