angular.module('one.widgets').factory('zemGridEndpointBreakdowns', function (zemPermissions) {
    var BASE_LEVEL_GROUP_NAME = 'Base level';
    var STRUCTURE_GROUP_NAME = 'By structure';
    var DELIVERY_GROUP_NAME = 'By delivery';
    var TIME_GROUP_NAME = 'By time';

    var BREAKDOWNS = {
        account: {name: 'By Account', query: constants.breakdown.ACCOUNT, report_query: 'Account'},
        campaign: {name: 'By Campaign', query: constants.breakdown.CAMPAIGN, report_query: 'Campaign'},
        adGroup: {name: 'By Ad Group', query: constants.breakdown.AD_GROUP, report_query: 'Ad Group'},
        contentAd: {name: 'By Content Ad', query: constants.breakdown.CONTENT_AD, report_query: 'Content Ad'},
        source: {name: 'By Source', query: constants.breakdown.MEDIA_SOURCE, report_query: 'Media Source'},
        publisher: {name: 'By Publisher', query: constants.breakdown.PUBLISHER, report_query: 'Publisher'},

        age: {name: 'Age', query: 'age', report_query: 'Age'},
        gender: {name: 'Gender', query: 'gender', report_query: 'Gender'},
        ageGender: {name: 'Age and Gender', query: 'age_gender', report_query: 'Age and Gender'},

        country: {name: 'Country', query: 'country', report_query: 'Country'},
        state: {name: 'State', query: 'state', report_query: 'State'},
        dma: {name: 'DMA', query: 'dma', report_query: 'DMA'},

        device: {name: 'Device', query: 'device_type', report_query: 'Device'},
        placementMedium: {name: 'Placement', query: 'placement_medium', report_query: 'Placement'},
        deviceOs: {name: 'Operating System', query: 'device_os', report_query: 'Operating System'},
        deviceOsVersion: {name: 'Operating System Version', query: 'device_os_version', report_query: 'Operating System Version'}, // eslint-disable-line max-len

        placementType: {name: 'Placement Type', query: 'placement_type', report_query: 'Placement Type'},
        videoPlaybackMethod: {name: 'Video Playback Method', query: 'video_playback_method', report_query: 'Video Playback Method'}, // eslint-disable-line max-len

        day: {name: 'By day', query: 'day', report_query: 'Day'},
        week: {name: 'By week', query: 'week', report_query: 'Week'},
        month: {name: 'By month', query: 'month', report_query: 'Month'},
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
        BREAKDOWNS.placementMedium,
        BREAKDOWNS.deviceOs,
        BREAKDOWNS.deviceOsVersion,

        BREAKDOWNS.placementType,
        BREAKDOWNS.videoPlaybackMethod,
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

    function getEntityLevelBreakdown (level) {
        switch (level) {
        case constants.level.ALL_ACCOUNTS: return BREAKDOWNS.account;
        case constants.level.ACCOUNTS: return BREAKDOWNS.campaign;
        case constants.level.CAMPAIGNS: return BREAKDOWNS.adGroup;
        case constants.level.AD_GROUPS: return BREAKDOWNS.contentAd;
        }
    }

    function getStructureBreakdowns (level, breakdown) {
        var entityBreakdown = getEntityLevelBreakdown(level);
        var childEntityBreakdown = ENTITY_BREAKDOWNS[ENTITY_BREAKDOWNS.indexOf(entityBreakdown) + 1];
        var structureBreakdowns = [];

        switch (breakdown) {
        case constants.breakdown.MEDIA_SOURCE:
            structureBreakdowns = [entityBreakdown, childEntityBreakdown]; break;
        case constants.breakdown.PUBLISHER:
            break;
        default:
            structureBreakdowns = [childEntityBreakdown, BREAKDOWNS.source];
        }

        // childEntityBreakdown can be undefined - filter it out on return
        return structureBreakdowns.filter(function (structureBreakdown) {
            return structureBreakdown !== undefined;
        });
    }

    function createBreakdownGroups (level, breakdown) {
        var breakdownGroups = {};

        // Base Level breakdown group; based on required breakdown
        var baseLevelBreakdown = getBaseLevelBreakdown(breakdown);
        breakdownGroups.base = {
            name: BASE_LEVEL_GROUP_NAME,
            breakdowns: [baseLevelBreakdown],
        };

        // Structure breakdown group; based on level and breakdown (i.g. dedicated tab)
        var structureBreakdowns = getStructureBreakdowns(level, breakdown);
        breakdownGroups.structure = {
            name: STRUCTURE_GROUP_NAME,
            breakdowns: structureBreakdowns,
        };

        // Delivery breakdown group
        breakdownGroups.delivery = {
            available: zemPermissions.hasPermission('zemauth.can_view_breakdown_by_delivery'),
            internal: zemPermissions.isPermissionInternal('zemauth.can_view_breakdown_by_delivery'),
            name: DELIVERY_GROUP_NAME,
            breakdowns: DELIVERY_BREAKDOWNS,
        };

        // Time breakdown group
        breakdownGroups.time = {
            name: TIME_GROUP_NAME,
            breakdowns: TIME_BREAKDOWNS,
        };

        return angular.copy(breakdownGroups);
    }

    return {
        BREAKDOWNS: BREAKDOWNS,
        ENTITY_BREAKDOWNS: ENTITY_BREAKDOWNS,
        TIME_BREAKDOWNS: TIME_BREAKDOWNS,
        getEntityLevelBreakdown: getEntityLevelBreakdown,
        createBreakdownGroups: createBreakdownGroups,
    };
});
