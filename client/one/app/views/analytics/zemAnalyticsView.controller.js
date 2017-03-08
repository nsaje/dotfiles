angular.module('one.views').controller('zemAnalyticsView', function ($stateParams, zemNavigationNewService) {
    var $ctrl = this;

    var DEFAULT_BREAKDOWN = {};
    DEFAULT_BREAKDOWN[constants.level.ALL_ACCOUNTS] = constants.breakdown.ACCOUNT;
    DEFAULT_BREAKDOWN[constants.level.ACCOUNTS] = constants.breakdown.CAMPAIGN;
    DEFAULT_BREAKDOWN[constants.level.CAMPAIGNS] = constants.breakdown.AD_GROUP;
    DEFAULT_BREAKDOWN[constants.level.AD_GROUPS] = constants.breakdown.CONTENT_AD;

    initialize();

    function initialize () {
        $ctrl.level = constants.levelStateParamToLevelMap[$stateParams.level];
        if (!$ctrl.level) return;

        $ctrl.id = $stateParams.id ? parseInt($stateParams.id) : null;
        $ctrl.breakdown =
            constants.breakdownStateParamToBreakdownMap[$stateParams.breakdown] || DEFAULT_BREAKDOWN[$ctrl.level];

        $ctrl.entity = zemNavigationNewService.getActiveEntity();
        if ($ctrl.entity === undefined) {
            var handler = zemNavigationNewService.onActiveEntityChange(function (event, entity) {
                $ctrl.entity = entity;
                handler();
            });
        }
    }
});
