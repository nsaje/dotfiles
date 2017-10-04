import core.bcm

from utils import numbers


class SourceTypeBCMMixin(object):
    def get_etfm_min_cpc(self, bcm_modifiers=None):
        min_cpc = self.min_cpc
        if not bcm_modifiers:
            return min_cpc

        etfm_min_cpc = core.bcm.calculations.apply_fee_and_margin(
            min_cpc, bcm_modifiers['fee'], bcm_modifiers['margin'])
        rounded = numbers.round_decimal_ceiling(etfm_min_cpc, places=3)
        return rounded

    def get_etfm_min_daily_budget(self, bcm_modifiers=None):
        min_daily_budget = self.min_daily_budget
        if not bcm_modifiers:
            return min_daily_budget

        etfm_min_daily_budget = core.bcm.calculations.apply_fee_and_margin(
            min_daily_budget, bcm_modifiers['fee'], bcm_modifiers['margin'])
        rounded = numbers.round_decimal_ceiling(etfm_min_daily_budget, places=0)
        return rounded

    def get_etfm_max_cpc(self, bcm_modifiers=None):
        max_cpc = self.max_cpc
        if not bcm_modifiers:
            return max_cpc
        etfm_max_cpc = core.bcm.calculations.apply_fee_and_margin(
            max_cpc, bcm_modifiers['fee'], bcm_modifiers['margin'])
        rounded = numbers.round_decimal_floor(etfm_max_cpc, places=3)
        return rounded

    def get_etfm_max_daily_budget(self, bcm_modifiers=None):
        max_daily_budget = self.max_daily_budget
        if not bcm_modifiers:
            return max_daily_budget

        etfm_max_daily_budget = core.bcm.calculations.apply_fee_and_margin(
            max_daily_budget, bcm_modifiers['fee'], bcm_modifiers['margin'])
        rounded = numbers.round_decimal_floor(etfm_max_daily_budget, places=0)
        return rounded
