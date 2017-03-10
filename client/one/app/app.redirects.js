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

    $urlRouterProvider.when('/:level/:id/:breakdownOrPage', ['$state', '$match', legacyRedirect]);
    $urlRouterProvider.when('/:level/:breakdownOrPage', ['$state', '$match', legacyRedirect]);
    $urlRouterProvider.when('/', ['$state', '$match', legacyRedirect]);

    function legacyRedirect ($state, $match) {
        var state = mapPagesToStates[$match.breakdownOrPage];
        var level = mapLegacyLevelToLevelParam[$match.level];
        var breakdown = mapLegacyBreakdownToBreakdownStateParam[$match.breakdownOrPage];

        state = state ? state : 'v2.analytics';
        level = level ? level : constants.levelStateParam.ACCOUNTS;

        var params = {
            id: $match.id,
            level: level,
            breakdown: breakdown
        };

        if ($match.breakdownOrPage === 'budget') {
            params.settings = true;
            params.settingsScrollTo = 'zemCampaignBudgetsSettings';
        }

        if ($match.breakdownOrPage === 'history') {
            params.history = true;

        }

        $state.go(state, params);
    }
});
