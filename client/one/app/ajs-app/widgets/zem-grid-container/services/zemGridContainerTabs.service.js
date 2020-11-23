var arrayHelpers = require('../../../../shared/helpers/array.helpers');
var commonHelpers = require('../../../../shared/helpers/common.helpers');

angular
    .module('one.widgets')
    .service('zemGridContainerTabsService', function(zemAuthStore) {
        var TABS = {
            accounts: {
                localStorageKey: 'tab.accounts',
                name: 'Accounts',
                breakdown: constants.breakdown.ACCOUNT,
                page: 1,
                pageSize: 50,
            },
            campaigns: {
                localStorageKey: 'tab.campaigns',
                name: 'Campaigns',
                breakdown: constants.breakdown.CAMPAIGN,
                page: 1,
                pageSize: 50,
            },
            ad_groups: {
                localStorageKey: 'tab.ad_groups',
                name: 'Ad groups',
                breakdown: constants.breakdown.AD_GROUP,
                page: 1,
                pageSize: 50,
            },
            content_ads: {
                localStorageKey: 'tab.content_ads',
                name: 'Content Ads',
                breakdown: constants.breakdown.CONTENT_AD,
                page: 1,
                pageSize: 50,
            },
            additional_breakdowns: {
                localStorageKey: 'tab.additional_breakdowns',
                name: null,
                breakdown: null,
                page: 1,
                pageSize: 50,
                options: [
                    {
                        name: 'Publishers',
                        breakdown: constants.breakdown.PUBLISHER,
                        page: 1,
                        pageSize: 50,
                    },
                    {
                        name: 'Placements',
                        breakdown: constants.breakdown.PLACEMENT,
                        page: 1,
                        pageSize: 50,
                    },
                    {
                        name: 'Media Sources',
                        breakdown: constants.breakdown.MEDIA_SOURCE,
                        page: 1,
                        pageSize: 50,
                    },
                    {
                        name: 'Country',
                        breakdown: constants.breakdown.COUNTRY,
                        page: 1,
                        pageSize: 50,
                    },
                    {
                        name: 'State / Region',
                        breakdown: constants.breakdown.STATE,
                        page: 1,
                        pageSize: 50,
                    },
                    {
                        name: 'DMA',
                        breakdown: constants.breakdown.DMA,
                        page: 1,
                        pageSize: 50,
                    },
                    {
                        name: 'Device',
                        breakdown: constants.breakdown.DEVICE,
                        page: 1,
                        pageSize: 50,
                    },
                    {
                        name: 'Environment',
                        breakdown: constants.breakdown.ENVIRONMENT,
                        page: 1,
                        pageSize: 50,
                    },
                    {
                        name: 'Operating System',
                        breakdown: constants.breakdown.OPERATING_SYSTEM,
                        page: 1,
                        pageSize: 50,
                    },
                    {
                        name: 'Browser',
                        breakdown: constants.breakdown.BROWSER,
                        page: 1,
                        pageSize: 50,
                        isNewFeature: true,
                    },
                    {
                        name: 'Connection Type',
                        breakdown: constants.breakdown.CONNECTION_TYPE,
                        page: 1,
                        pageSize: 50,
                        isNewFeature: true,
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
                addTab(
                    options,
                    getAdditionalBreakdownsForEntityType(undefined)
                );
            } else if (entity.type === constants.entityType.ACCOUNT) {
                addTab(options, TABS.campaigns);
                addTab(
                    options,
                    getAdditionalBreakdownsForEntityType(entity.type)
                );
            } else if (entity.type === constants.entityType.CAMPAIGN) {
                addTab(options, TABS.ad_groups);
                addTab(
                    options,
                    getAdditionalBreakdownsForEntityType(entity.type)
                );
                addTab(options, TABS.insights);
            } else if (entity.type === constants.entityType.AD_GROUP) {
                addTab(options, TABS.content_ads);
                addTab(
                    options,
                    getAdditionalBreakdownsForEntityType(entity.type)
                );
            }
            return options;
        }

        function getAdditionalBreakdownsForEntityType(entityType) {
            var displayedOptions = TABS.additional_breakdowns.options.filter(
                function(x) {
                    return (
                        arrayHelpers.isEmpty(x.displayOnEntityTypes) ||
                        (commonHelpers.isDefined(entityType) &&
                            x.displayOnEntityTypes.includes(entityType))
                    );
                }
            );

            var result = {};
            Object.assign(result, TABS.additional_breakdowns);
            result.options = displayedOptions;

            return result;
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
                    var hasPermissions = zemAuthStore.hasPermission(
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
                tabCopy.options.sort(function(a, b) {
                    var textA = a.name.toUpperCase();
                    var textB = b.name.toUpperCase();
                    return textA.localeCompare(textB);
                });
                tabs.push(tabCopy);
            }
        }

        function addTabItem(tabs, tab) {
            if (tab.permissions) {
                var hasPermissions = zemAuthStore.hasPermission(
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
