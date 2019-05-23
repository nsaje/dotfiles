angular
    .module('one.widgets')
    .factory('zemGridEndpointBreakdowns', function(zemPermissions, zemUtils) {
        var BASE_LEVEL_GROUP_NAME = 'Base level';
        var STRUCTURE_GROUP_NAME = 'By structure';
        var DELIVERY_GROUP_NAME = 'By delivery';
        var TIME_GROUP_NAME = 'By time';

        var BREAKDOWNS = {
            /* eslint-disable max-len */
            account: {
                name: 'By Account',
                query: constants.breakdown.ACCOUNT,
                report_query: 'Account',
                shown: true,
            },
            campaign: {
                name: 'By Campaign',
                query: constants.breakdown.CAMPAIGN,
                report_query: 'Campaign',
                shown: true,
            },
            adGroup: {
                name: 'By Ad Group',
                query: constants.breakdown.AD_GROUP,
                report_query: 'Ad Group',
                shown: true,
            },
            contentAd: {
                name: 'By Content Ad',
                query: constants.breakdown.CONTENT_AD,
                report_query: 'Content Ad',
                shown: true,
            },
            source: {
                name: 'By Source',
                query: constants.breakdown.MEDIA_SOURCE,
                report_query: 'Media Source',
                shown: true,
            },
            publisher: {
                name: 'By Publisher',
                query: constants.breakdown.PUBLISHER,
                report_query: 'Publisher',
                shown: true,
            },

            age: {
                name: 'Age',
                query: 'age',
                report_query: 'Age',
                shown: 'zemauth.can_view_breakdown_by_delivery_extended',
                internal: 'zemauth.can_view_breakdown_by_delivery_extended',
            },
            gender: {
                name: 'Gender',
                query: 'gender',
                report_query: 'Gender',
                shown: 'zemauth.can_view_breakdown_by_delivery_extended',
                internal: 'zemauth.can_view_breakdown_by_delivery_extended',
            },
            ageGender: {
                name: 'Age and Gender',
                query: 'age_gender',
                report_query: 'Age and Gender',
                shown: 'zemauth.can_view_breakdown_by_delivery_extended',
                internal: 'zemauth.can_view_breakdown_by_delivery_extended',
            },

            country: {
                name: 'Country',
                query: 'country',
                report_query: 'Country',
                shown: 'zemauth.can_view_breakdown_by_delivery',
                internal: 'zemauth.can_view_breakdown_by_delivery',
            },
            region: {
                name: 'State / Region',
                query: 'region',
                report_query: 'State / Region',
                shown: 'zemauth.can_view_breakdown_by_delivery',
                internal: 'zemauth.can_view_breakdown_by_delivery',
            },
            dma: {
                name: 'DMA',
                query: 'dma',
                report_query: 'DMA',
                shown: 'zemauth.can_view_breakdown_by_delivery',
                internal: 'zemauth.can_view_breakdown_by_delivery',
            },

            device: {
                name: 'Device',
                query: 'device_type',
                report_query: 'Device',
                shown: 'zemauth.can_view_breakdown_by_delivery',
                internal: 'zemauth.can_view_breakdown_by_delivery',
            },
            deviceOs: {
                name: 'Operating System',
                query: 'device_os',
                report_query: 'Operating System',
                shown: 'zemauth.can_view_breakdown_by_delivery',
                internal: 'zemauth.can_view_breakdown_by_delivery',
            },
            deviceOsVersion: {
                name: 'Operating System Version',
                query: 'device_os_version',
                report_query: 'Operating System Version',
                shown: 'zemauth.can_view_breakdown_by_delivery_extended',
                internal: 'zemauth.can_view_breakdown_by_delivery_extended',
            },

            placementMedium: {
                name: 'Placement',
                query: 'placement_medium',
                report_query: 'Placement',
                shown: 'zemauth.can_view_breakdown_by_delivery',
                internal: 'zemauth.can_view_breakdown_by_delivery',
            },

            placementType: {
                name: 'Placement Type',
                query: 'placement_type',
                report_query: 'Placement Type',
                shown: 'zemauth.can_view_breakdown_by_delivery_extended',
                internal: 'zemauth.can_view_breakdown_by_delivery_extended',
            },
            videoPlaybackMethod: {
                name: 'Video Playback Method',
                query: 'video_playback_method',
                report_query: 'Video Playback Method',
                shown: 'zemauth.can_view_breakdown_by_delivery_extended',
                internal: 'zemauth.can_view_breakdown_by_delivery_extended',
            },

            day: {
                name: 'By day',
                query: 'day',
                report_query: 'Day',
                shown: true,
            },
            week: {
                name: 'By week',
                query: 'week',
                report_query: 'Week',
                shown: true,
            },
            month: {
                name: 'By month',
                query: 'month',
                report_query: 'Month',
                shown: true,
            },
            /* eslint-enable max-len */
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
            BREAKDOWNS.country,
            BREAKDOWNS.region,
            BREAKDOWNS.dma,
            BREAKDOWNS.device,
            BREAKDOWNS.placementMedium,
            BREAKDOWNS.deviceOs,
        ]);

        var DELIVERY_BREAKDOWNS = [
            BREAKDOWNS.age,
            BREAKDOWNS.gender,
            BREAKDOWNS.ageGender,

            BREAKDOWNS.country,
            BREAKDOWNS.region,
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

        function getBaseLevelBreakdown(breakdown) {
            // Find requested base level breakdown
            return BASE_LEVEL_BREAKDOWNS.filter(function(b) {
                return b.query === breakdown;
            })[0];
        }

        function getEntityLevelBreakdown(level) {
            switch (level) {
                case constants.level.ALL_ACCOUNTS:
                    return BREAKDOWNS.account;
                case constants.level.ACCOUNTS:
                    return BREAKDOWNS.campaign;
                case constants.level.CAMPAIGNS:
                    return BREAKDOWNS.adGroup;
                case constants.level.AD_GROUPS:
                    return BREAKDOWNS.contentAd;
            }
        }

        function getStructureBreakdowns(level, breakdown) {
            var entityBreakdown = getEntityLevelBreakdown(level);
            var childEntityBreakdown =
                ENTITY_BREAKDOWNS[
                    ENTITY_BREAKDOWNS.indexOf(entityBreakdown) + 1
                ];
            var structureBreakdowns = [];

            switch (breakdown) {
                case constants.breakdown.MEDIA_SOURCE:
                    structureBreakdowns = [
                        entityBreakdown,
                        childEntityBreakdown,
                    ];
                    break;
                case constants.breakdown.PUBLISHER:
                case constants.breakdown.COUNTRY:
                case constants.breakdown.STATE:
                case constants.breakdown.DMA:
                case constants.breakdown.DEVICE:
                case constants.breakdown.PLACEMENT:
                case constants.breakdown.OPERATING_SYSTEM:
                    break;
                default:
                    structureBreakdowns = [
                        childEntityBreakdown,
                        BREAKDOWNS.source,
                    ];
            }

            // childEntityBreakdown can be undefined - filter it out on return
            return structureBreakdowns.filter(function(structureBreakdown) {
                return structureBreakdown !== undefined;
            });
        }

        function getDeliveryBreakdowns(breakdown) {
            switch (breakdown) {
                case constants.breakdown.COUNTRY:
                case constants.breakdown.STATE:
                case constants.breakdown.DMA:
                case constants.breakdown.DEVICE:
                case constants.breakdown.PLACEMENT:
                case constants.breakdown.OPERATING_SYSTEM:
                    return [];
                default:
                    return checkPermissions(DELIVERY_BREAKDOWNS);
            }
        }

        function getTimeBreakdowns(breakdown) {
            switch (breakdown) {
                case constants.breakdown.COUNTRY:
                case constants.breakdown.STATE:
                case constants.breakdown.DMA:
                case constants.breakdown.DEVICE:
                case constants.breakdown.PLACEMENT:
                case constants.breakdown.OPERATING_SYSTEM:
                    return [];
                default:
                    return TIME_BREAKDOWNS;
            }
        }

        function createBreakdownGroups(level, breakdown) {
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
                available: zemPermissions.hasPermission(
                    'zemauth.can_view_breakdown_by_delivery'
                ),
                internal: zemPermissions.isPermissionInternal(
                    'zemauth.can_view_breakdown_by_delivery'
                ),
                name: DELIVERY_GROUP_NAME,
                breakdowns: getDeliveryBreakdowns(breakdown),
            };

            // Time breakdown group
            breakdownGroups.time = {
                name: TIME_GROUP_NAME,
                breakdowns: getTimeBreakdowns(breakdown),
            };

            return angular.copy(breakdownGroups);
        }

        function checkPermissions(breakdowns) {
            var copy = [];

            breakdowns.forEach(function(br) {
                var brCopy = angular.copy(br);
                brCopy.internal = zemUtils.convertPermission(
                    br.internal,
                    zemPermissions.isPermissionInternal
                );
                brCopy.shown = zemUtils.convertPermission(
                    br.shown,
                    zemPermissions.hasPermission
                );

                copy.push(brCopy);
            });

            return copy;
        }

        return {
            BREAKDOWNS: BREAKDOWNS,
            ENTITY_BREAKDOWNS: ENTITY_BREAKDOWNS,
            TIME_BREAKDOWNS: TIME_BREAKDOWNS,
            getEntityLevelBreakdown: getEntityLevelBreakdown,
            createBreakdownGroups: createBreakdownGroups,
        };
    });
