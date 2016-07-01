/* globals oneApp, constants */
'use strict';

oneApp.factory('zemGridEndpointBreakdowns', [function () {
    var BASE_LEVEL_GROUP_NAME = 'Base level';
    var STRUCTURE_GROUP_NAME = 'By structure';
    var DELIVERY_GROUP_NAME = 'By delivery';
    var TIME_GROUP_NAME = 'By time';

    var BREAKDOWNS = {
        account: {name: 'By Account', query: constants.breakdown.ACCOUNT},
        campaign: {name: 'By Campaign', query: constants.breakdown.CAMPAIGN},
        adGroup: {name: 'By Ad Group', query: constants.breakdown.AD_GROUP},
        contentAd: {name: 'By Content Ad', query: constants.breakdown.CONTENT_AD},
        source: {name: 'By Source', query: constants.breakdown.MEDIA_SOURCE},
        publisher: {name: 'By Publisher', query: constants.breakdown.PUBLISHER},

        age: {name: 'Age', query: 'age'},
        gender: {name: 'Gender', query: 'gender'},
        ageGender: {name: 'Age and Gender', query: 'age_gender'},
        country: {name: 'Country', query: 'country'},
        state: {name: 'State', query: 'state'},
        dma: {name: 'DMA', query: 'dma'},
        device: {name: 'Device', query: 'device_type'},

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

    function getBaseLevelBreakdown (breakdown) {
        // Find requested base level breakdown
        return BASE_LEVEL_BREAKDOWNS.filter(function (b) {
            return b.query === breakdown;
        })[0];
    }

    function getStructureBreakdowns (baseLevelBreakdown) {
        // Find structure breakdowns for requested level (only available on entity breakdowns)
        var structureBreakdowns = [];
        var entityBreakdownIdx = ENTITY_BREAKDOWNS.indexOf(baseLevelBreakdown);
        if (entityBreakdownIdx >= 0) {
            // Direct child entity breakdown is also added to structure breakdowns if defined
            if (entityBreakdownIdx + 1 < ENTITY_BREAKDOWNS.length) {
                structureBreakdowns.push(ENTITY_BREAKDOWNS[entityBreakdownIdx + 1]);
            }
            // Source and Publisher breakdowns are always available
            structureBreakdowns.push(BREAKDOWNS.source);
            structureBreakdowns.push(BREAKDOWNS.publisher);
        }

        return structureBreakdowns;
    }

    function createBreakdownGroups (level, breakdown) {
        var breakdownGroups = [];

        // Base Level breakdown group; based on required breakdown
        var baseLevelBreakdown = getBaseLevelBreakdown(breakdown);
        breakdownGroups.push ({
            name: BASE_LEVEL_GROUP_NAME,
            breakdowns: [baseLevelBreakdown],
        });

        // Structure breakdown group; based on level and breakdown (i.g. dedicated tab)
        var structureBreakdowns = getStructureBreakdowns(baseLevelBreakdown);
        if (structureBreakdowns.length > 0) {
            breakdownGroups.push ({
                name: STRUCTURE_GROUP_NAME,
                breakdowns: structureBreakdowns,
            });
        }

        // Delivery breakdown group
        breakdownGroups.push ({
            name: DELIVERY_GROUP_NAME,
            breakdowns: DELIVERY_BREAKDOWNS,
        });

        // Time breakdown group
        breakdownGroups.push ({
            name: TIME_GROUP_NAME,
            breakdowns: TIME_BREAKDOWNS,
        });

        return breakdownGroups;
    }

    return {
        BREAKDOWNS: BREAKDOWNS,
        createBreakdownGroups: createBreakdownGroups,
    };
}]);
