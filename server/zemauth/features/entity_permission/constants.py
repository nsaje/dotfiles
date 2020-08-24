from utils.constant_base import ConstantBase


class Permission(ConstantBase):
    READ = "read"
    WRITE = "write"
    USER = "user"
    BUDGET = "budget"
    BUDGET_MARGIN = "budget_margin"  # NOT USED
    AGENCY_SPEND_MARGIN = "agency_spend_margin"
    MEDIA_COST_DATA_COST_LICENCE_FEE = "media_cost_data_cost_licence_fee"
    BASE_COSTS_SERVICE_FEE = "base_costs_service_fee"
    RESTAPI = "restapi"  # NOT USED

    _VALUES = {
        READ: "View accounts, campaigns, ad groups and ads.",
        WRITE: "Edit accounts, campaigns, ad groups and ads.",
        USER: "Manage other users.",
        BUDGET: "Allocate budgets to campaigns.",
        BUDGET_MARGIN: "Configure campaign budget margin.",
        AGENCY_SPEND_MARGIN: "View agency spend and margin.",
        MEDIA_COST_DATA_COST_LICENCE_FEE: "View media cost, data cost and licence fee.",
        BASE_COSTS_SERVICE_FEE: "View base media cost, base data cost and service fee.",
        RESTAPI: "RESTAPI access",
    }


REPORTING_PERMISSIONS = [
    Permission.AGENCY_SPEND_MARGIN,
    Permission.MEDIA_COST_DATA_COST_LICENCE_FEE,
    Permission.BASE_COSTS_SERVICE_FEE,
]


class AccessLevel(ConstantBase):
    NONE = 0
    ACCOUNT_MANAGER = 1
    AGENCY_MANAGER = 2
    INTERNAL_USER = 3
