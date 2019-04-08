var arrayHelpers = require('../../../../shared/helpers/array.helpers');

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
                name: null,
                breakdown: null,
                options: [
                    {
                        name: 'Publishers',
                        breakdown: constants.breakdown.PUBLISHER,
                        permissions: 'zemauth.can_see_publishers_all_levels',
                    },
                    {
                        name: 'Media Sources',
                        breakdown: constants.breakdown.MEDIA_SOURCE,
                    },
                    {
                        name: 'Country',
                        breakdown: constants.breakdown.COUNTRY,
                        permissions:
                            'zemauth.can_see_top_level_delivery_breakdowns',
                    },
                    {
                        name: 'State / Region',
                        breakdown: constants.breakdown.STATE,
                        permissions:
                            'zemauth.can_see_top_level_delivery_breakdowns',
                    },
                    {
                        name: 'DMA',
                        breakdown: constants.breakdown.DMA,
                        permissions:
                            'zemauth.can_see_top_level_delivery_breakdowns',
                    },
                    {
                        name: 'Device',
                        breakdown: constants.breakdown.DEVICE,
                        permissions:
                            'zemauth.can_see_top_level_delivery_breakdowns',
                    },
                    {
                        name: 'Placement',
                        breakdown: constants.breakdown.PLACEMENT,
                        permissions:
                            'zemauth.can_see_top_level_delivery_breakdowns',
                    },
                    {
                        name: 'Operating System',
                        breakdown: constants.breakdown.OPERATING_SYSTEM,
                        permissions:
                            'zemauth.can_see_top_level_delivery_breakdowns',
                    },
                ],
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
                addTab(options, TABS.accounts);
                addTab(options, TABS.additional_breakdowns);
            } else if (entity.type === constants.entityType.ACCOUNT) {
                addTab(options, TABS.campaigns);
                addTab(options, TABS.additional_breakdowns);
            } else if (entity.type === constants.entityType.CAMPAIGN) {
                addTab(options, TABS.ad_groups);
                addTab(options, TABS.additional_breakdowns);
                addTab(options, TABS.insights);
            } else if (entity.type === constants.entityType.AD_GROUP) {
                addTab(options, TABS.content_ads);
                addTab(options, TABS.additional_breakdowns);
            }
            return options;
        }

        //
        // Private methods
        //

        function hasOptions(tab) {
            return !arrayHelpers.isEmpty(tab.options);
        }

        function addTab(tabs, tab) {
            if (hasOptions(tab)) {
                addTabItemWithOptions(tabs, tab);
            } else {
                addTabItem(tabs, tab);
            }
        }

        function addTabItemWithOptions(tabs, tab) {
            var options = angular.copy(tab.options).filter(function(option) {
                if (option.permissions) {
                    var hasPermissions = zemPermissions.hasPermission(
                        option.permissions
                    );
                    if (hasPermissions) {
                        return option;
                    }
                } else {
                    return option;
                }
            });
            if (options && options.length > 0) {
                var tabCopy = angular.copy(tab);
                tabCopy.name = options[0].name;
                tabCopy.breakdown = options[0].breakdown;
                tabCopy.options = options.length > 1 ? options : null;
                tabs.push(tabCopy);
            }
        }

        function addTabItem(tabs, tab) {
            if (tab.permissions) {
                var hasPermissions = zemPermissions.hasPermission(
                    tab.permissions
                );
                if (hasPermissions) {
                    tabs.push(angular.copy(tab));
                }
            } else {
                tabs.push(angular.copy(tab));
            }
        }
    });
