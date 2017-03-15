/* global angular */

angular.module('one').config(function ($urlRouterProvider) {
    //
    // This file contains redirects from legacy routes to new ones
    //
    if (!window.APP || !window.APP.USE_NEW_ROUTING) return;

    var mapLegacyLevelToLevelParam = {};
    mapLegacyLevelToLevelParam['all_accounts'] = constants.levelStateParam.ACCOUNTS;
    mapLegacyLevelToLevelParam['accounts'] = constants.levelStateParam.ACCOUNT;
    mapLegacyLevelToLevelParam['campaigns'] = constants.levelStateParam.CAMPAIGN;
    mapLegacyLevelToLevelParam['ad_groups'] = constants.levelStateParam.AD_GROUP;

    var mapLegacyBreakdownToBreakdownStateParam = {};
    mapLegacyBreakdownToBreakdownStateParam['accounts'] = null;
    mapLegacyBreakdownToBreakdownStateParam['campaigns'] = null;
    mapLegacyBreakdownToBreakdownStateParam['ad_groups'] = null;
    mapLegacyBreakdownToBreakdownStateParam['ads'] = null;
    mapLegacyBreakdownToBreakdownStateParam['sources'] = constants.breakdownStateParam.SOURCES;
    mapLegacyBreakdownToBreakdownStateParam['publishers'] = constants.breakdownStateParam.PUBLISHERS;
    mapLegacyBreakdownToBreakdownStateParam['insights'] = constants.breakdownStateParam.INSIGHTS;

    var mapPagesToStates = angular.extend({}, mapLegacyBreakdownToBreakdownStateParam);
    angular.forEach(mapPagesToStates, function (value, key) { mapPagesToStates[key] = 'v2.analytics'; });
    mapPagesToStates['scheduled_reports'] = 'v2.reports';
    mapPagesToStates['scheduled_reports_v2'] = 'v2.reports';
    mapPagesToStates['pixels'] = 'v2.pixels';
    mapPagesToStates['users'] = 'v2.users';
    mapPagesToStates['publishergroups'] = 'v2.publisherGroups';
    mapPagesToStates['credit'] = 'v2.accountCredit';
    mapPagesToStates['credit_v2'] = 'v2.accountCredit';
    mapPagesToStates['archived'] = 'v2.archived';

    $urlRouterProvider.when('/:level/:id/:breakdownOrPage', ['$rootScope', '$state', '$match', legacyRedirect]);
    $urlRouterProvider.when('/:level/:breakdownOrPage', ['$rootScope', '$state', '$match', legacyRedirect]);
    $urlRouterProvider.when('/', ['$rootScope ', '$state', '$match', legacyRedirect]);

    function legacyRedirect ($rootScope, $state, $match) {
        var state = mapPagesToStates[$match.breakdownOrPage];
        var level = mapLegacyLevelToLevelParam[$match.level];
        var breakdown = mapLegacyBreakdownToBreakdownStateParam[$match.breakdownOrPage];

        state = state ? state : 'v2.analytics';
        level = level ? level : constants.levelStateParam.ACCOUNTS;

        var params = {
            id: $match.id ? parseInt($match.id) : null,
            level: level,
            breakdown: breakdown,
            settings: null,
            settingsScrollTo: null,
            history: null,
        };

        if ($match.breakdownOrPage === 'budget') {
            params.settings = true;
            params.settingsScrollTo = 'zemCampaignBudgetsSettings';
        }

        if ($match.breakdownOrPage === 'history') {
            params.history = true;
        }

        // [WORKAROUND] Avoid state reload if user already on the correct one
        var avoidReload = ($state.is(state) && params.level === $state.params.level && params.id === $state.params.id);
        if (avoidReload) $rootScope.$broadcast('$zemStateChangeStart');
        $state.go(state, params, {reload: !avoidReload, notify: !avoidReload}).then(function () {
            if (avoidReload) $rootScope.$broadcast('$zemStateChangeSuccess');
        });
    }
});
