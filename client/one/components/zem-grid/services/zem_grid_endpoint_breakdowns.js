/* globals oneApp, angular */
'use strict';

oneApp.factory('zemGridEndpointBreakdowns', [function () {
    var BREAKDOWN_GROUPS = [
        {
            name: 'Base level',
            breakdowns: [
                // Base level breakdown - defined later based on Endpoint type
            ],
        },
        {
            name: 'By structure',
            breakdowns: [
                {name: 'By Campaign', query: 'campaign'},
                {name: 'By Ad Group', query: 'ad_group'},
                {name: 'By Content Ad', query: 'content_ad'},
                {name: 'By Source', query: 'source'},
                {name: 'By Publisher', query: 'publisher'},
                // Type specific structure breakdown - Defined later based on Endpoint type
            ],
        },
        {
            name: 'By delivery',
            breakdowns: [
                {name: 'Age', query: 'age'},
                {name: 'Gender', query: 'gender'},
                {name: 'Age and Gender', query: 'agegender'},
                {name: 'Country', query: 'country'},
                {name: 'State', query: 'state'},
                {name: 'DMA', query: 'dma'},
                {name: 'Device', query: 'device'},
            ],
        },
        {
            name: 'By time',
            breakdowns: [
                {name: 'By day', query: 'day'},
                {name: 'By week', query: 'week'},
                {name: 'By month', query: 'month'},
            ],
        },
    ];

    var BASE_LEVEL_BREAKDOWNS = [
        {name: 'By Account', query: 'account'},
        {name: 'By Campaign', query: 'campaign'},
        {name: 'By Ad Group', query: 'ad_group'},
        {name: 'By Content Ad', query: 'content_ad'},
        {name: 'By Source', query: 'source'},
        {name: 'By Publisher', query: 'publisher'},
    ];

    function createBreakdownGroups (baseLevel, baseLevelBreakdown) {
        var breakdownGroups = angular.copy(BREAKDOWN_GROUPS);

        // Find requested base level breakdown
        breakdownGroups[0].breakdowns = BASE_LEVEL_BREAKDOWNS.filter(function (b) {
            return b.query === baseLevelBreakdown;
        });

        // TODO: Structure breakdown is possible for levels lower then requested baseLevel

        return breakdownGroups;
    }

    return {
        createBreakdownGroups: createBreakdownGroups,
    };
}]);
