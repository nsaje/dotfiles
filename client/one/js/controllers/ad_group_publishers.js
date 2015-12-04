/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupPublishersCtrl', ['$scope', '$state', '$location', '$timeout', '$window', 'api', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', function ($scope, $state, $location, $timeout, $window, api, zemPostclickMetricsService, zemFilterService, zemUserSettings) {
    $scope.selectedTotals = true;
    $scope.selectedColumnsCount = 0;
    $scope.constants = constants;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartHidden = false;
    $scope.chartMetricOptions = [];
    $scope.chartGoalMetrics = null;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-cost';
    $scope.localStoragePrefix = 'adGroupPublishers';
    $scope.sizeRange = [5, 10, 20, 50];
    $scope.size = $scope.sizeRange[0];
    $scope.rows = [];
    $scope.isSyncInProgress = false;
    $scope.pagination = {
        currentPage: 1
    };
    // this will be set to true whenever blacklisted and not blacklisted
    // publishers have been manually selected
    $scope.mixedBlacklistEnabledSelection = false;

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    $scope.selectionMenuConfig = {
        hideCombo: true
    };
    // selection settings - all or specific publishers can be selected
    $scope.selectedAll = false;
    $scope.selectedPublisherStatus = {};

    $scope.bulkBlacklistActions = [{
        name: 'Blacklist in this adgroup',
        value: 'blacklist-adgroup',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status')
    }, {
        name: 'Blacklist in this campaign',
        value: 'blacklist-campaign',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Blacklist in this account',
        value: 'blacklist-account',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Blacklist globally',
        value: 'blacklist-global',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_global_publisher_blacklist_status')
    }];

    $scope.bulkEnableActions = [{
        name: 'Re-enable in this adgroup',
        value: 'enable-adgroup',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status')
    }, {
        name: 'Re-enable in this campaign',
        value: 'enable-campaign',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Re-enable in this account',
        value: 'enable-account',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Re-enable globally',
        value: 'enable-global',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_global_publisher_blacklist_status')
    }];

    $scope.calculatePublisherHash = function (row) {
        // very simplistic hash to allow blacklist selection
        return row.exchange + ' ' + row.domain;
    };

    $scope.setAllBulkAction = function (action, enabled) {
        $scope.setBulkAction(null, action, enabled);
    };

    $scope.setBulkAction = function (level, action, enabled) {
        var postfix = level || '.*',
            matchRegex = new RegExp('^'.concat(action, '-', postfix, '$'));

        $scope.bulkBlacklistActions.forEach(function (bulkAction) {
            if (matchRegex.test(bulkAction.value)) {
                bulkAction.disabled = !enabled;
            }
        });
        $scope.bulkEnableActions.forEach(function (bulkAction) {
            if (matchRegex.test(bulkAction.value)) {
                bulkAction.disabled = !enabled;
            }
        });
    };

    $scope.selectedPublisherChanged = function (row, checked) {
        var numNotSelected = 0,
            countBlacklistedSelected = 0,
            countNonBlacklistedSelected = 0,
            countAllSelected = 0,
            maxBlacklistedLevel = null,
            levels = [
                constants.publisherBlacklistLevel.ADGROUP,
                constants.publisherBlacklistLevel.CAMPAIGN,
                constants.publisherBlacklistLevel.ACCOUNT,
                constants.publisherBlacklistLevel.GLOBAL
            ];

        $scope.selectedPublisherStatus[$scope.calculatePublisherHash(row)] = {
            "checked": checked,
            "source_id": row.source_id,
            "domain": row.domain,
            "blacklisted": row.blacklisted,
            "blacklisted_level": row.blacklisted_level
        };

        Object.keys($scope.selectedPublisherStatus).forEach(function (publisherId) {
            if (!$scope.selectedPublisherStatus[publisherId].checked) {
                numNotSelected += 1;
            }
        });

        Object.keys($scope.selectedPublisherStatus).forEach(function (key) {
            var entry = $scope.selectedPublisherStatus[key];
            if (entry.checked) {
                if (entry.blacklisted === 'Blacklisted') {
                    countBlacklistedSelected += 1;
                    if (maxBlacklistedLevel === null || $scope.levelGt(entry.blacklisted_level, maxBlacklistedLevel)) {
                        maxBlacklistedLevel = entry.blacklisted_level;
                    }
                } else if (entry.blacklisted === 'Active') {
                    countNonBlacklistedSelected += 1;
                }
            }
        });
        countAllSelected = countBlacklistedSelected + countNonBlacklistedSelected;

        if (countBlacklistedSelected > 0 && countNonBlacklistedSelected > 0) {
            $scope.mixedBlacklistEnabledSelection = true;
            $scope.setAllBulkAction('enable', false);
            $scope.setAllBulkAction('blacklist', false);
        } else if (countBlacklistedSelected > 0 || countNonBlacklistedSelected > 0) {
            $scope.mixedBlacklistEnabledSelection = false;
            $scope.setAllBulkAction('enable', countBlacklistedSelected > 0);
            $scope.setAllBulkAction('blacklist', countNonBlacklistedSelected > 0);
        } else {
            $scope.mixedBlacklistEnabledSelection = false;
            $scope.setAllBulkAction('enable', countAllSelected > 0);
            $scope.setAllBulkAction('blacklist', countAllSelected > 0);
        }

        if (!$scope.mixedBlacklistEnabledSelection && (maxBlacklistedLevel !== null)) {
            if (countBlacklistedSelected > 0) {
                levels.forEach(function (level) {
                    // user can only enable blacklist on currently
                    // blacklisted level
                    var enabled = $scope.levelEq(level, maxBlacklistedLevel);
                    $scope.setBulkAction(level, 'enable', enabled);

                    var blacklistedEnabled = $scope.levelGt(level, maxBlacklistedLevel);
                    // user can always blacklist on higher level
                    // than currently blacklisted
                    $scope.setBulkAction(level, 'blacklist', blacklistedEnabled);
                });
            }

            if (countNonBlacklistedSelected > 0) {
                levels.forEach(function (level) {
                    var enabled = $scope.levelGt(level, maxBlacklistedLevel);
                    // user can always blacklist on higher level
                    // than currently blacklisted
                    $scope.setBulkAction(level, 'blacklist', enabled);
                });
            }
        }

        if ($scope.selectedAll) {
            $scope.selectionMenuConfig.partialSelection = numNotSelected > 0;
        }
    };

    $scope.compareLevels = function (level1, level2) {
        var map = { };
        map[constants.publisherBlacklistLevel.ADGROUP] = 1;
        map[constants.publisherBlacklistLevel.CAMPAIGN] = 2;
        map[constants.publisherBlacklistLevel.ACCOUNT] = 3;
        map[constants.publisherBlacklistLevel.GLOBAL] = 4;
        if (map[level1] < map[level2]) {
            return -1;
        }
        if (map[level1] === map[level2])  {
            return 0;
        }
        return 1;
    };

    $scope.levelEq = function (level1, level2) {
        return $scope.compareLevels(level1, level2) === 0;
    };

    $scope.levelGt = function (level1, level2) {
        return $scope.compareLevels(level1, level2) > 0;
    };

    $scope.selectionMenuConfig.selectAllCallback = function (selected) {
        $scope.selectionMenuConfig.partialSelection = false;
        $scope.selectedAll = selected;
        $scope.selectedPublisherStatus = {};

        if (selected) {
            $scope.updatePublisherSelection();
        } else {
            $scope.clearPublisherSelection();
        }
    };

    $scope.clearPublisherSelection = function () {
        $scope.rows.forEach(function (row) {
            row.publisherSelected = false;
        });
    };

    $scope.updatePublisherSelection = function () {
        $scope.rows.forEach(function (row) {
            if (row !== undefined) {
                row.disabledSelection = !row.can_blacklist_publisher;
                if (!row.can_blacklist_publisher) {
                    row.blacklistInfo = "This publisher can't be blacklisted because the media source doesn't support publisher blacklisting. ";
                    row.blacklistInfo = row.blacklistInfo.concat("Contact your account manager for further details.");
                } else {
                    row.blacklistInfo = null;
                }

                if (row.can_blacklist_publisher) {
                    var rowId = $scope.calculatePublisherHash(row);
                    if ($scope.selectedPublisherStatus[rowId] !== undefined) {
                        row.publisherSelected = $scope.selectedPublisherStatus[rowId].checked;
                    } else if ($scope.selectedAll) {
                        row.publisherSelected = true;
                    } else {
                        row.publisherSelected = false;
                    }
                }
            }
        });
    };

    $scope.isAnythingSelected = function () {
        if ($scope.mixedBlacklistEnabledSelection) {
            return false;
        }

        if ($scope.selectedAll) {
            return true;
        }


        for (var publisherId in $scope.selectedPublisherStatus) {
            if ($scope.selectedPublisherStatus.hasOwnProperty(publisherId)
                    && $scope.selectedPublisherStatus[publisherId].checked) {
                return true;
            }
        }

        return false;
    };

    var pollSyncStatus = function() {
        if ($scope.isSyncInProgress) {
            $timeout(function() {
                api.checkPublisherBlacklistSyncProgress.get($state.params.id).then(
                    function(data) {
                        $scope.isSyncInProgress = data.data.is_sync_in_progress;
                        if ($scope.isSyncInProgress === false) {
                            // we found out that the sync is no longer in progress
                            // time to reload the data
                            getTableData();
                            getDailyStats();
                        }
                    },
                    function(data) {
                        // error
                        $scope.isSyncInProgress = false;
                    }
                ).finally(function() {
                    pollSyncStatus();
                });
            }, 10000);
        }
    };

    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;
    };

    $scope.executeBulkAction = function (composedAction) {
        if (!$scope.isAnythingSelected()) {
            return;
        }

        var publishersSelected = [],
            publishersNotSelected = [],
            splitAction = composedAction.split('-'),
            action = splitAction[0],
            level = splitAction[1],
            state = null;

        if (level === constants.publisherBlacklistLevel.GLOBAL) {
            if (!confirm("This action will affect all accounts. Are you sure you want to proceed?")) {
                return;               
            }
        }

        Object.keys($scope.selectedPublisherStatus).forEach(function (publisherId) {
            if ($scope.selectedPublisherStatus[publisherId] !== undefined) {
                if ($scope.selectedPublisherStatus[publisherId].checked) {
                    publishersSelected.push($scope.selectedPublisherStatus[publisherId]);
                } else {
                    publishersNotSelected.push($scope.selectedPublisherStatus[publisherId]);
                }
            }
        });

        
        if (action === 'enable') {
            state = constants.publisherStatus.ENABLED;
        } else {
            state = constants.publisherStatus.BLACKLISTED;
        }
        bulkUpdatePublishers(publishersSelected, publishersNotSelected, state, level);
    };

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
                'publisherSelected',
                'blacklisted',
                'domain',
                'domain_link',
                'exchange',
                'cost',
                'data_cost',
                'cpc', 
                'clicks', 
                'impressions', 
                'ctr'
            ]
        }
    ];

    $scope.columns = [{
            name: '',
            field: 'publisherSelected',
            type: 'checkbox',
            showSelectionMenu: true,
            shown: $scope.hasPermission('zemauth.can_see_publisher_blacklist_status'),
            hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status'),
            checked: true,
            totalRow: false,
            unselectable: true,
            order: false,
            popupField: 'blacklistInfo',
            selectCallback: $scope.selectedPublisherChanged,
            disabled: false,
            selectionMenuConfig: $scope.selectionMenuConfig
        },
        {

            name: 'Status',
            field: 'blacklisted',
            checked: true,
            extraTdCss: 'no-wrap',
            type: 'textWithPopup',
            popupField: 'blacklisted_level_description',
            shown: $scope.hasPermission('zemauth.can_see_publisher_blacklist_status'),
            help: 'Blacklisted status of a publisher.',
            totalRow: false,
            order: false,
            initialOrder: 'asc'
        },
        {
            name: 'Domain',
            field: 'domain',
            unselectable: false,
            checked: true,
            type: 'clickPermissionOrText',
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'A publisher where your content is being promoted.',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'Link',
            field: 'domain_link',
            unselectable: false,
            checked: true,
            type: 'link',
            shown: true,
            totalRow: false,
            help: 'Link to a publisher where your content is being promoted.',
            order: false,
            initialOrder: 'asc'
        },
        {
            name: 'Media Source',
            field: 'exchange',
            unselectable: false,
            checked: true,
            type: 'clickPermissionOrText',
            shown: true,
            totalRow: false,
            help: 'An exchange where your content is being promoted.',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            shown: true,
            help: "Amount spent per publisher.",
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Data Cost',
            field: 'data_cost',
            checked: true,
            type: 'currency',
            help: 'Additional targeting/segmenting costs.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_data_cost'),
            shown: $scope.hasPermission('zemauth.can_view_data_cost')
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: "The average CPC.",
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
            shown: true,
            help: 'The number of times a content ad has been clicked.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number',
            shown: true,
            help: 'The number of times a content ad has been displayed.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'CTR',
            field: 'ctr',
            checked: true,
            type: 'percent',
            shown: true,
            defaultValue: '0.0%',
            help: 'The number of clicks divided by the number of impressions.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }
    ];

    $scope.loadRequestInProgress = false;

    $scope.orderTableData = function(order) {
        $scope.order = order;
        getTableData();
    };


    var bulkUpdatePublishers = function (publishersSelected, publishersNotSelected, state, level) {
        api.adGroupPublishersState.save(
            $state.params.id,
            state,
            level,
            $scope.dateRange.startDate, 
            $scope.dateRange.endDate, 
            publishersSelected,
            publishersNotSelected,
            $scope.selectedAll
        ).then(function () {
            $scope.triggerSync();

            // clear publisher selection
            $scope.selectionMenuConfig.partialSelection = false;
            $scope.selectedAll = false;
            $scope.selectedPublisherStatus = {};
            $scope.clearPublisherSelection();
        });
    };


    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.adGroupPublishersTable.get($state.params.id, $scope.pagination.currentPage, $scope.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {

                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.totals.checked = $scope.selectedTotals;
                $scope.lastChange = data.lastChange;
                $scope.pagination = data.pagination;

                $scope.updatePublisherSelection();
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };
/*    if ($window.isDemo) {
        $window.demoActions.refreshAdGroupSourcesTable = getTableData;
    }*/

    var getDailyStatsMetrics = function () {
        var values = $scope.chartMetricOptions.map(function (option) {
            return option.value;
        });

        // always query for default metrics
        var metrics = [constants.chartMetric.CLICKS, constants.chartMetric.IMPRESSIONS];
        if (values.indexOf($scope.chartMetric1) === -1) {
            $scope.chartMetric1 = constants.chartMetric.CLICKS;
        } else {
            metrics.push($scope.chartMetric1);
        }

        if ($scope.chartMetric2 !== 'none' && values.indexOf($scope.chartMetric2) === -1) {
            $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
        } else {
            metrics.push($scope.chartMetric2);
        }

        return metrics;
    };

    var setChartOptions = function (goals) {
        $scope.chartMetricOptions = options.adGroupChartMetrics;
    };

    var getDailyStats = function () {
        $scope.selectedPublisherIds = [];
        $scope.selectedTotals = true;
        api.dailyStats.listPublishersStats($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedPublisherIds,  $scope.selectedTotals, getDailyStatsMetrics()).then(
            function (data) {
                setChartOptions(data.goals);

                $scope.chartData = data.chartData;
                $scope.chartGoalMetrics = data.goals;
            },
            function (data) {
                // error
                return;
            }
        ); 
    };

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;
        $scope.chartBtnTitle = $scope.chartHidden ? 'Show chart' : 'Hide chart';

        $timeout(function() {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    var hasMetricData = function (metric) {
        var hasData = false;
        $scope.chartData.forEach(function (group) {
            if (group.seriesData[metric] !== undefined) {
                hasData = true;
            }
        });

        return hasData;
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!hasMetricData($scope.chartMetric1)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!hasMetricData($scope.chartMetric2)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    // From parent scope (mainCtrl).
    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
            return;
        }

        getTableData();
        getDailyStats();
    });

    $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        getTableData();
        getDailyStats();
    }, true);

    $scope.$watch(zemFilterService.getBlacklistedPublishers, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        getTableData();
        getDailyStats();

    }, true);


    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if (newValue === true && oldValue === false) {
            pollSyncStatus();            
        }
    }, true);

    $scope.init = function() {
        var data = $scope.adGroupData[$state.params.id];

        var page = parseInt($location.search().page);
        if (isNaN(page)) {
            page = data && data.page;
        }
        var size = parseInt($location.search().size || '0');

        userSettings.registerWithoutWatch('chartMetric1');
        userSettings.registerWithoutWatch('chartMetric2');
        userSettings.register('order');
        userSettings.register('size');
        userSettings.registerGlobal('chartHidden');

        if (size !== 0 && $scope.size !== size) {
            $scope.size = size;
        }
        // if nothing in local storage or page query var set first as default
        if ($scope.size === 0) {
            $scope.size = $scope.sizeRange[0];
        }


        setChartOptions();

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
            $scope.setAdGroupData('page', page);
            $location.search('page', page);
        }

        $scope.loadPage();

        $scope.getAdGroupState();	// To display message if the adgroup is paused

        getTableData();
        getDailyStats();
        zemFilterService.setShowBlacklistedPublishers(true);
    };


    $scope.loadPage = function(page) {
        if(page && page > 0 && page <= $scope.pagination.numPages) {
            $scope.pagination.currentPage = page;
        }

        if ($scope.pagination.currentPage && $scope.pagination.size) {
            $location.search('page', $scope.pagination.currentPage);
            $scope.setAdGroupData('page', $scope.pagination.currentPage);

            getTableData();
        }
    };

    $scope.$watch('size', function(newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.loadPage();
        }
    });


    $scope.$on('$destroy', function () {
        zemFilterService.setShowBlacklistedPublishers(false);
        $timeout.cancel($scope.lastChangeTimeout);
    });

    $scope.init();
}]);
