angular
    .module('one.widgets')
    .service('zemGridContainerTabsService', function(zemPermissions) {
        var TABS = {
            accounts: {
                localStorageKey: 'tab.accounts',
                name: 'Accounts',
                breakdown: constants.breakdown.ACCOUNT,
            },
            campaigns: {
                localStorageKey: 'tab.campaigns',
                name: 'Campaigns',
                breakdown: constants.breakdown.CAMPAIGN,
            },
            ad_groups: {
                localStorageKey: 'tab.ad_groups',
                name: 'Ad groups',
                breakdown: constants.breakdown.AD_GROUP,
            },
            content_ads: {
                localStorageKey: 'tab.content_ads',
                name: 'Content Ads',
                breakdown: constants.breakdown.CONTENT_AD,
            },
            additional_breakdowns: {
                localStorageKey: 'tab.additional_breakdowns',
                name: 'Media Sources',
                breakdown: constants.breakdown.MEDIA_SOURCE,
                options: [
                    {
                        name: 'Media Sources',
                        breakdown: constants.breakdown.MEDIA_SOURCE,
                    },
                    {
                        name: 'Country',
                        breakdown: constants.breakdown.COUNTRY,
                    },
                    {
                        name: 'State',
                        breakdown: constants.breakdown.STATE,
                    },
                    {
                        name: 'DMA',
                        breakdown: constants.breakdown.DMA,
                    },
                    {
                        name: 'Device',
                        breakdown: constants.breakdown.DEVICE,
                    },
                    {
                        name: 'Placement',
                        breakdown: constants.breakdown.PLACEMENT,
                    },
                    {
                        name: 'Operating System',
                        breakdown: constants.breakdown.OPERATING_SYSTEM,
                    },
                ],
            },
            publishers: {
                localStorageKey: 'tab.publishers',
                name: 'Publishers',
                breakdown: constants.breakdown.PUBLISHER,
            },
            insights: {
                localStorageKey: 'tab.insights',
                name: 'Content Insights',
                breakdown: 'insights',
            },
        };

        this.createTabOptions = createTabOptions;

        //
        // Public methods
        //
        function createTabOptions(entity) {
            var options = [];
            if (!entity) {
                options = [
                    angular.copy(TABS.accounts),
                    angular.copy(getAdditionalBreakdownsTab()),
                ];
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_see_publishers_all_levels'
                    )
                ) {
                    options.push(angular.copy(TABS.publishers));
                }
            } else if (entity.type === constants.entityType.ACCOUNT) {
                options = [
                    angular.copy(TABS.campaigns),
                    angular.copy(getAdditionalBreakdownsTab()),
                ];
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_see_publishers_all_levels'
                    )
                ) {
                    options.push(angular.copy(TABS.publishers));
                }
            } else if (
                entity &&
                entity.type === constants.entityType.CAMPAIGN
            ) {
                options = [
                    angular.copy(TABS.ad_groups),
                    angular.copy(getAdditionalBreakdownsTab()),
                    angular.copy(TABS.insights),
                ];
                if (
                    zemPermissions.hasPermission(
                        'zemauth.can_see_publishers_all_levels'
                    )
                ) {
                    options.splice(2, 0, angular.copy(TABS.publishers));
                }
            } else if (
                entity &&
                entity.type === constants.entityType.AD_GROUP
            ) {
                options = [
                    angular.copy(TABS.content_ads),
                    angular.copy(getAdditionalBreakdownsTab()),
                    angular.copy(TABS.publishers),
                ];
            }
            return options;
        }

        //
        // Private methods
        //
        function getAdditionalBreakdownsTab() {
            if (
                zemPermissions.hasPermission(
                    'zemauth.can_see_top_level_delivery_breakdowns'
                )
            ) {
                return TABS.additional_breakdowns;
            }
            var tab = angular.copy(TABS.additional_breakdowns);
            tab.options = [];
            return tab;
        }
    });
