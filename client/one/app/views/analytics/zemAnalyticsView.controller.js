angular.module('one.views').controller('zemAnalyticsView', function ($scope, $state, zemNavigationNewService) {
    var $ctrl = this;

    var DEFAULT_BREAKDOWN = {};
    DEFAULT_BREAKDOWN[constants.level.ALL_ACCOUNTS] = constants.breakdown.ACCOUNT;
    DEFAULT_BREAKDOWN[constants.level.ACCOUNTS] = constants.breakdown.CAMPAIGN;
    DEFAULT_BREAKDOWN[constants.level.CAMPAIGNS] = constants.breakdown.AD_GROUP;
    DEFAULT_BREAKDOWN[constants.level.AD_GROUPS] = constants.breakdown.CONTENT_AD;

    initialize();

    function initialize () {
        $ctrl.level = constants.levelStateParamToLevelMap[$state.params.level];
        if (!$ctrl.level) return;

        $ctrl.entity = zemNavigationNewService.getActiveEntity();
        if ($ctrl.entity === undefined) {
            var handler = zemNavigationNewService.onActiveEntityChange(function (event, entity) {
                $ctrl.entity = entity;
                handler();
            });
        }

        updateBreakdownParams();

        // [WORKAROUND] Avoid zemAnalyticsView re-initialization
        // Ui-Router does not have mechanism to reuse states with dynamic parameters therefor we navigate to
        // this state with {notify: false}, which in turn will change params but will not recreate the state.
        // This is used by zemGridContainer, to avoid reinitialization of zemInfobox and zemChart components.
        $scope.$watchCollection(function () { return $state.params; }, updateBreakdownParams);
    }

    function updateBreakdownParams () {
        $ctrl.breakdown =
            constants.breakdownStateParamToBreakdownMap[$state.params.breakdown]
            || DEFAULT_BREAKDOWN[$ctrl.level];

        // FIXME: Chart Workaround - Fallback to default breakdown in case of INSIGHTS breakdown
        $ctrl.chartBreakdown = $ctrl.breakdown === constants.breakdown.INSIGHTS
            ? DEFAULT_BREAKDOWN[$ctrl.level] : $ctrl.breakdown;
    }
});
