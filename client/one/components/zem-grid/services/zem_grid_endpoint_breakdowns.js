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
            name: 'By structure',
            breakdowns: [
                // Type specific structure breakdown - Defined later based on Endpoint type
                {name: 'By media source', query: 'source'},
                {name: 'By publishers', query: 'publishers'},
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

    var STRUCTURE_LEVEL_BREAKDOWNS = [
        {name: 'By Campaign', query: 'campaign'},
        {name: 'By Ad Group', query: 'ad_group'},
        {name: 'By Content Ad', query: 'content_ad'},
    ];

    function createBreakdownGroups (baseLevel, baseLevelBreakdown) {
        var breakdownGroups = angular.copy(BREAKDOWN_GROUPS);

        // Find requested base level breakdown
        breakdownGroups[0].breakdowns = BASE_LEVEL_BREAKDOWNS.filter(function (b) {
            return b.query === baseLevelBreakdown;
        });

        // Structure breakdown is possible for levels lower then requested baseLevel
        for (var i = STRUCTURE_LEVEL_BREAKDOWNS.length - 1; i >= 0; --i) {
            var structureBreakdown = STRUCTURE_LEVEL_BREAKDOWNS[i];
            if (structureBreakdown.query === baseLevel) break;

            breakdownGroups[2].breakdowns.unshift(structureBreakdown);
        }

        return breakdownGroups;
    }

    return {
        createBreakdownGroups: createBreakdownGroups,
    };
}]);
