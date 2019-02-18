from utils import lc_helper


class CpcConstraintInstanceMixin:
    def __str__(self):
        desc = "CPC constraint"
        if self.source:
            desc += " on source {}".format(self.source.name)
        else:
            desc += " on all sources"
        desc += " with"

        if hasattr(self, "bcm_min_cpc") and self.bcm_min_cpc:
            desc += " min. CPC {}".format(lc_helper.default_currency(self.bcm_min_cpc))
        if hasattr(self, "bcm_max_cpc") and self.bcm_max_cpc:
            if hasattr(self, "bcm_min_cpc") and self.bcm_min_cpc:
                desc += " and"
            desc += " max. CPC {}".format(lc_helper.default_currency(self.bcm_max_cpc))
        return desc
