from utils.constant_base import ConstantBase


class DetailedDeliveryStatus(ConstantBase):
    ACTIVE = "active"
    ACTIVE_PRICE_DISCOVERY = "active-price-discovery"  # TODO: RTAP: remove this after Phase 1
    INACTIVE = "inactive"
    STOPPED = "stopped"
    AUTOPILOT = "autopilot"  # TODO: RTAP: remove this after Phase 1
    BUDGET_OPTIMIZATION = "budget-optimization"
    OPTIMAL_BID = "optimal-bid"
    BUDGET_OPTIMIZATION_OPTIMAL_BID = "budget-optimization-optimal-bid"
    CAMPAIGNSTOP_STOPPED = "campaignstop-stopped"
    CAMPAIGNSTOP_LOW_BUDGET = "campaignstop-low-budget"
    CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT = (
        "campaignstop-pending-budget-autopilot"  # TODO: RTAP: remove this after Phase 1
    )
    CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION = "campaignstop-pending-budget-budget-optimization"
    CAMPAIGNSTOP_PENDING_BUDGET_OPTIMAL_BID = "campaignstop-pending-budget-optimal-bid"
    CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION_OPTIMAL_BID = (
        "campaignstop-pending-budget-budget-optimization-optimal-bid"
    )
    CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE_PRICE_DISCOVERY = (
        "campaignstop-pending-budget-active-price-discovery"  # TODO: RTAP: remove this after Phase 1
    )
    CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE = "campaignstop-pending-budget-active"
    DISABLED = "disabled"

    _VALUES = {
        ACTIVE: "Active",
        ACTIVE_PRICE_DISCOVERY: "Active - Price Discovery",  # TODO: RTAP: remove this after Phase 1
        INACTIVE: "Inactive",
        STOPPED: "Stopped",
        AUTOPILOT: "Autopilot",  # TODO: RTAP: remove this after Phase 1
        BUDGET_OPTIMIZATION: "Budget optimization",
        OPTIMAL_BID: "Optimal bid optimization",
        BUDGET_OPTIMIZATION_OPTIMAL_BID: "Budget and optimal bid optimization",
        CAMPAIGNSTOP_STOPPED: "Stopped - Out of budget",
        CAMPAIGNSTOP_LOW_BUDGET: "Active - Running out of budget",  # TODO: RTAP: remove this after Phase 1
        CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT: "Active - Pending budget allocations",
        CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION: "Active - Pending budget allocations",
        CAMPAIGNSTOP_PENDING_BUDGET_OPTIMAL_BID: "Active - Pending budget allocations",
        CAMPAIGNSTOP_PENDING_BUDGET_BUDGET_OPTIMIZATION_OPTIMAL_BID: "Active - Pending budget allocations",
        CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE_PRICE_DISCOVERY: "Active - Pending budget allocations",  # TODO: RTAP: remove this after Phase 1
        CAMPAIGNSTOP_PENDING_BUDGET_ACTIVE: "Active - Pending budget allocations",
        DISABLED: "Disabled - Contact Zemanta CSM",
    }


class DeliveryStatus(ConstantBase):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    STOPPED = "STOPPED"
    DISABLED = "DISABLED"

    _VALUES = {ACTIVE: "Active", INACTIVE: "Inactive", STOPPED: "Stopped", DISABLED: "Disabled - Contact Zemanta CSM"}
