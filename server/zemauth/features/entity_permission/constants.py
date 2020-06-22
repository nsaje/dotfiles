from utils.constant_base import ConstantBase


class Permission(ConstantBase):
    READ = "read"
    WRITE = "write"
    USER = "user"
    BUDGET = "budget"
    BUDGET_MARGIN = "budget_margin"
    AGENCY_SPEND_MARGIN = "agency_spend_margin"
    MEDIA_COST_DATA_COST_LICENCE_FEE = "media_cost_data_cost_licence_fee"
    BASE_COSTS_SERVICE_FEE = "base_costs_service_fee"
    RESTAPI = "restapi"

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
