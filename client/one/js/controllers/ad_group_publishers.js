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
    $scope.pagination = {
        currentPage: 1
    };
    // this will be set to true whenever blacklisted and not blacklisted
    // publishers have been manually selected
    $scope.mixedBlacklistEnabledSelection = false;


    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    $scope.selectionMenuConfig = {};
    // selection settings - all or specific publishers can be selected
    $scope.selectedAll = false;
    $scope.selectedPublisherStatus = {};

    $scope.bulkActions = [{
        name: 'Blacklist in this adgroup',
        value: 'blacklist',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status')
    }, {
        name: 'Re-enable in this adgroup',
        value: 'enable',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status')
    }];

    $scope.calculatePublisherHash = function(row) {
        // very simplistic hash to allow blacklist selection
        return row['exchange'] + ' ' + row['domain'];
    };

    $scope.selectedPublisherChanged = function(row, checked) {
        $scope.selectedPublisherStatus[$scope.calculatePublisherHash(row)] = {
            "checked": checked,
            "source": row['exchange'],
            "domain": row['domain']
        };

        var numSelected = 0,
            numNotSelected = 0,
            countBlacklistedSelected = 0,
            countNonBlacklistedSelected = 0;

        Object.keys($scope.selectedPublisherStatus).forEach(function (publisherId) {
            if ($scope.selectedPublisherStatus[publisherId].checked) {
                numSelected += 1;

            } else {
                numNotSelected += 1;
            }
        });

        $scope.rows.forEach(function (currentRow) {
            if (currentRow.publisher_selected) {
                if (currentRow.blacklisted === 'Blacklisted') {
                    countBlacklistedSelected += 1
                } else if (currentRow.blacklisted === 'Active') {
                    countNonBlacklistedSelected += 1
                }
            }
        });

        if (countBlacklistedSelected > 0 && countNonBlacklistedSelected > 0) {
            $scope.mixedBlacklistEnabledSelection = true;
        } else {
            $scope.mixedBlacklistEnabledSelection = false;
        }

        if ($scope.selectedAll) {
            $scope.selectionMenuConfig.partialSelection = numNotSelected > 0;
        }  
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
            row.publisher_selected = false;
        });
    };

    $scope.updatePublisherSelection = function() {
        $scope.rows.forEach(function(row) {
            var row_id = $scope.calculatePublisherHash(row);
            if ($scope.selectedPublisherStatus[row_id] !== undefined) {
                row.publisher_selected = $scope.selectedPublisherStatus[row_id].checked;
            } else if ($scope.selectedAll) {
                row.publisher_selected = true;
            } else {
                row.publisher_selected = false;
            }
        });
    };

    $scope.isAnythingSelected = function() {
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

    $scope.executeBulkAction = function (action) {
        if (!$scope.isAnythingSelected()) {
            return;
        }

        var publishersSelected = [],
            publishersNotSelected = [];

        Object.keys($scope.selectedPublisherStatus).forEach(function (publisherId) {
            if ($scope.selectedPublisherStatus[publisherId] !== undefined) {
                if ($scope.selectedPublisherStatus[publisherId].checked) {
                    publishersSelected.push($scope.selectedPublisherStatus[publisherId]);
                } else {
                    publishersNotSelected.push($scope.selectedPublisherStatus[publisherId]);
                }
            }
        });

        switch (action) {
            case 'blacklist':
                bulkUpdatePublishers(
                    publishersSelected,
                    publishersNotSelected,
                    constants.publisherStatus.BLACKLISTED
                );
                break;
            case 'enable':
                bulkUpdatePublishers(
                    publishersSelected,
                    publishersNotSelected,
                    constants.publisherStatus.ENABLED
                );
                break;
        }
    };

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
               'publisher_selected',
               'blacklisted',
               'domain',
               'domain_link',
               'exchange',
               'cost', 
               'cpc', 
               'clicks', 
               'impressions', 
               'ctr', 
            ]
        }
    ];

    $scope.columns = [{
            name: '',
            field: 'publisher_selected',
            type: 'checkbox',
            showSelectionMenu: true,
            shown: $scope.hasPermission('zemauth.can_see_publisher_blacklist_status'),
            hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status'),
            checked: true,
            totalRow: false,
            unselectable: true,
            order: false,
            selectCallback: $scope.selectedPublisherChanged,
            disabled: false,
            selectionMenuConfig: $scope.selectionMenuConfig
        },
        {

            name: 'Status',
            field: 'blacklisted',
            checked: true,
            extraTdCss: 'no-wrap',
            type: 'text',
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


    var bulkUpdatePublishers = function (publishersSelected, publishersNotSelected, state) {
        api.adGroupPublishersState.save(
            $state.params.id,
            state,
            $scope.dateRange.startDate, 
            $scope.dateRange.endDate, 
            publishersSelected,
            publishersNotSelected,
            $scope.selectedAll
        ).then(function () {
            getTableData();

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

        getDailyStats();
        getTableData();
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
