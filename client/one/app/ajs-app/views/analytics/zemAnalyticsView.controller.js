require('./zemAnalyticsView.partial.less');

angular
    .module('one.views')
    .controller('zemAnalyticsView', function(
        $scope,
        $state,
        zemNavigationNewService,
        zemPermissions
    ) {
        var $ctrl = this;

        var DEFAULT_BREAKDOWN = {};
        DEFAULT_BREAKDOWN[constants.level.ALL_ACCOUNTS] =
            constants.breakdown.ACCOUNT;
        DEFAULT_BREAKDOWN[constants.level.ACCOUNTS] =
            constants.breakdown.CAMPAIGN;
        DEFAULT_BREAKDOWN[constants.level.CAMPAIGNS] =
            constants.breakdown.AD_GROUP;
        DEFAULT_BREAKDOWN[constants.level.AD_GROUPS] =
            constants.breakdown.CONTENT_AD;

        initialize();

        function initialize() {
            updateView();
            $scope.$on('$zemStateChangeSuccess', updateView);
        }

        function updateView() {
            var level =
                constants.levelStateParamToLevelMap[$state.params.level];
            if (!level) return;

            var entity = zemNavigationNewService.getActiveEntity();
            if (entity !== undefined) {
                setModel(entity, level, $state.params.breakdown);
            } else {
                var handler = zemNavigationNewService.onActiveEntityChange(
                    function(event, entity) {
                        setModel(entity, level, $state.params.breakdown);
                        handler();
                    }
                );
            }
        }

        function setModel(entity, level, breakdownStateParam) {
            $ctrl.level = level;
            $ctrl.entity = entity;
            $ctrl.breakdown = getBreakdown(level, breakdownStateParam);
            $ctrl.chartBreakdown = getChartBreakdown(level, $ctrl.breakdown);
            $ctrl.initialized = true;
        }

        function getBreakdown(level, breakdownStateParam) {
            var breakdown =
                constants.breakdownStateParamToBreakdownMap[
                    breakdownStateParam
                ];
            if (breakdown && canSeeBreakdown(breakdown)) {
                return breakdown;
            }
            return DEFAULT_BREAKDOWN[level];
        }

        function getChartBreakdown(level, breakdown) {
            return breakdown === constants.breakdown.INSIGHTS
                ? DEFAULT_BREAKDOWN[level]
                : breakdown;
        }

        function canSeeBreakdown(breakdown) {
            if (
                breakdown === constants.breakdown.COUNTRY ||
                breakdown === constants.breakdown.STATE ||
                breakdown === constants.breakdown.DMA ||
                breakdown === constants.breakdown.DEVICE ||
                breakdown === constants.breakdown.PLACEMENT ||
                breakdown === constants.breakdown.OPERATING_SYSTEM
            ) {
                return zemPermissions.hasPermission(
                    'zemauth.can_see_top_level_delivery_breakdowns'
                );
            }
            return true;
        }
    });
