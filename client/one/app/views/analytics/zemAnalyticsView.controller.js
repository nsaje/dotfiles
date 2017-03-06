angular.module('one.views').controller('zemAnalyticsView', function ($stateParams) {
    var $ctrl = this;

    var DEFAULT_BREAKDOWN = {};
    DEFAULT_BREAKDOWN[constants.level.ALL_ACCOUNTS] = constants.breakdown.ACCOUNT;
    DEFAULT_BREAKDOWN[constants.level.ACCOUNTS] = constants.breakdown.CAMPAIGN;
    DEFAULT_BREAKDOWN[constants.level.CAMPAIGNS] = constants.breakdown.AD_GROUP;
    DEFAULT_BREAKDOWN[constants.level.AD_GROUPS] = constants.breakdown.CONTENT_AD;

    initialize();

    function initialize () {
        $ctrl.level = getLevelFromParams($stateParams.level);
        $ctrl.breakdown = getBreakdownFromParams($stateParams.breakdown, $ctrl.level);
        $ctrl.id = $stateParams.id ? parseInt($stateParams.id) : null;
    }

    function getLevelFromParams (level) {
        switch (level) {
        case 'accounts': return constants.level.ALL_ACCOUNTS;
        case 'account': return constants.level.ACCOUNTS;
        case 'campaign': return constants.level.CAMPAIGNS;
        case 'adgroup': return constants.level.AD_GROUPS;
        }
    }

    function getBreakdownFromParams (breakdown, level) {
        switch (breakdown) {
        case 'sources': return constants.breakdown.MEDIA_SOURCE;
        case 'publishers': return constants.breakdown.PUBLISHER;
        default: return DEFAULT_BREAKDOWN[level];
        }
    }
});
