/* globals oneApp, angular, constants */
'use strict';

oneApp.factory('zemGridEndpointBreakdowns', [function () {
    var BREAKDOWNS = {
        account: {name: 'By Account', query: constants.breakdown.ACCOUNT},
        campaign: {name: 'By Campaign', query: constants.breakdown.CAMPAIGN},
        adGroup: {name: 'By Ad Group', query: constants.breakdown.AD_GROUP},
        contentAd: {name: 'By Content Ad', query: constants.breakdown.CONTENT_AD},
        source: {name: 'By Source', query: constants.breakdown.MEDIA_SOURCE},
        publisher: {name: 'By Publisher', query: constants.breakdown.PUBLISHER},

        age: {name: 'Age', query: 'age'},
        gender: {name: 'Gender', query: 'gender'},
        ageGender: {name: 'Age and Gender', query: 'agegender'},
        country: {name: 'Country', query: 'country'},
        state: {name: 'State', query: 'state'},
        dma: {name: 'DMA', query: 'dma'},
        device: {name: 'Device', query: 'device'},

        day: {name: 'By day', query: 'day'},
        week: {name: 'By week', query: 'week'},
        month: {name: 'By month', query: 'month'},
    };


    var ENTITY_BREAKDOWNS = [
        BREAKDOWNS.account,
        BREAKDOWNS.campaign,
        BREAKDOWNS.adGroup,
        BREAKDOWNS.contentAd,
    ];

    var BASE_LEVEL_BREAKDOWNS = ENTITY_BREAKDOWNS.concat([
        BREAKDOWNS.source,
        BREAKDOWNS.publisher,
    ]);

    var DELIVERY_BREAKDOWNS = [
        BREAKDOWNS.age,
        BREAKDOWNS.gender,
        BREAKDOWNS.ageGender,
        BREAKDOWNS.country,
        BREAKDOWNS.state,
        BREAKDOWNS.dma,
        BREAKDOWNS.device,
    ];

    var TIME_BREAKDOWNS = [
        BREAKDOWNS.day,
        BREAKDOWNS.week,
        BREAKDOWNS.month,
    ];

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
                // Type specific structure breakdown - Defined later based on Endpoint type
            ],
        },
        {
            name: 'By delivery',
            breakdowns: DELIVERY_BREAKDOWNS,
        },
        {
            name: 'By time',
            breakdowns: TIME_BREAKDOWNS,
        },
    ];

    function getBaseLevelBreakdown (breakdown) {
        // Find requested base level breakdown
        return BASE_LEVEL_BREAKDOWNS.filter(function (b) {
            return b.query === breakdown;
        })[0];
    }

    function getStructureBreakdowns (baseLevelBreakdown) {
        // Find structure breakdowns for requested level (only available on entity breakdowns)
        var structureBreakdowns = [];
        var entityBreakdowndIdx = ENTITY_BREAKDOWNS.indexOf(baseLevelBreakdown);
        if (entityBreakdowndIdx >= 0) {
            // Direct child entity breakdown is also added to structure breakdowns if defined
            if (entityBreakdowndIdx + 1 < ENTITY_BREAKDOWNS.length) {
                structureBreakdowns.push(ENTITY_BREAKDOWNS[entityBreakdowndIdx + 1]);
            }
            // Source and Publisher breakdowns are always available
            structureBreakdowns.push(BREAKDOWNS.source);
            structureBreakdowns.push(BREAKDOWNS.publisher);
        }

        return structureBreakdowns;
    }

    function createBreakdownGroups (level, breakdown) {
        var breakdownGroups = angular.copy(BREAKDOWN_GROUPS);

        // Add missing breakdown groups (those that depends on level and breakdown)
        var baseLevelBreakdown = getBaseLevelBreakdown(breakdown);
        breakdownGroups[0].breakdowns = [baseLevelBreakdown];
        var structureBreakdowns = getStructureBreakdowns(baseLevelBreakdown);
        if (structureBreakdowns.length > 0)
            breakdownGroups[1].breakdowns = structureBreakdowns;
        else
            breakdownGroups.splice(1, 1); // Remove group if there is no structure breakdowns

        return breakdownGroups;
    }

    return {
        BREAKDOWNS: BREAKDOWNS,
        createBreakdownGroups: createBreakdownGroups,
    };
}]);
