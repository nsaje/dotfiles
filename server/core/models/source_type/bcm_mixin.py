import core.bcm


class SourceTypeBCMMixin(object):
    def get_etfm_min_cpc(self, bcm_modifiers=None):
        return core.bcm.calculations.calculate_min_bid_value(self.min_cpc, bcm_modifiers)

    def get_etfm_max_cpc(self, bcm_modifiers=None):
        return core.bcm.calculations.calculate_max_bid_value(self.max_cpc, bcm_modifiers)

    def get_etfm_min_cpm(self, bcm_modifiers=None):
        return core.bcm.calculations.calculate_min_bid_value(self.min_cpm, bcm_modifiers)

    def get_etfm_max_cpm(self, bcm_modifiers=None):
        return core.bcm.calculations.calculate_max_bid_value(self.max_cpm, bcm_modifiers)

    def get_etfm_min_daily_budget(self, bcm_modifiers=None):
        return core.bcm.calculations.calculate_min_daily_budget(self.min_daily_budget, bcm_modifiers)

    def get_etfm_max_daily_budget(self, bcm_modifiers=None):
        return core.bcm.calculations.calculate_max_daily_budget(self.max_daily_budget, bcm_modifiers)
