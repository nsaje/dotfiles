angular
    .module('one.services')
    .service('zemCostModeService', function(zemPubSubService, zemAuthStore) {
        // eslint-disable-line max-len
        var TOGGLABLE_COST_MODES = [
            constants.costMode.PUBLIC,
            constants.costMode.PLATFORM,
        ];

        this.setCostMode = setCostMode;
        this.getCostMode = getCostMode;
        this.getOppositeCostMode = getOppositeCostMode;

        this.toggleCostMode = toggleCostMode;
        this.isTogglableCostMode = isTogglableCostMode;
        this.isToggleAllowed = isToggleAllowed;

        this.TOGGLABLE_COST_MODES = TOGGLABLE_COST_MODES;

        this.onCostModeUpdate = onCostModeUpdate;

        var pubSub = zemPubSubService.createInstance();
        var EVENTS = {
            ON_COST_MODE_UPDATE: 'zem-cost-mode-on-update',
        };

        var globalCostMode = constants.costMode.PUBLIC;

        //
        // Public methods
        //
        function setCostMode(costMode) {
            globalCostMode = costMode;
            pubSub.notify(EVENTS.ON_COST_MODE_UPDATE, getCostMode());
        }

        function getCostMode() {
            return globalCostMode;
        }

        function getOppositeCostMode(costMode) {
            if (costMode === constants.costMode.PUBLIC)
                return constants.costMode.PLATFORM;
            if (costMode === constants.costMode.PLATFORM)
                return constants.costMode.PUBLIC;
            return costMode;
        }

        function toggleCostMode() {
            setCostMode(getOppositeCostMode(getCostMode()));
        }

        function isTogglableCostMode(costMode) {
            return TOGGLABLE_COST_MODES.indexOf(costMode) >= 0;
        }

        function isToggleAllowed() {
            return zemAuthStore.hasPermission(
                'zemauth.can_switch_between_cost_breakdowns'
            );
        }

        //
        // Events
        //
        function onCostModeUpdate(callback) {
            return pubSub.register(EVENTS.ON_COST_MODE_UPDATE, callback);
        }
    });
