/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupPublishersCtrl', ['$scope', '$state', '$location', '$timeout', '$window', 'api', 'zemCustomTableColsService', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', function ($scope, $state, $location, $timeout, $window, api, zemCustomTableColsService, zemPostclickMetricsService, zemFilterService, zemUserSettings) {
    $scope.isIncompletePostclickMetrics = false;
    $scope.constants = constants;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartHidden = false;
    $scope.chartMetricOptions = [];
    $scope.chartGoalMetrics = null;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-cost';

    $scope.sizeRange = [5, 10, 20, 50];
    $scope.size = $scope.sizeRange[0];
    $scope.pagination = {
        currentPage: 1
    };


    var userSettings = zemUserSettings.getInstance($scope, 'adGroupPublishers');

    $scope.exportOptions = [
        {name: 'By Day (CSV)', value: 'csv'},
        {name: 'By Day (Excel)', value: 'excel'}
    ];



    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
               'exchange',
               'cost', 'cost_data',
               'cpc', 'clicks', 'impressions', 'ctr', 
            ]
        }
    ];

    $scope.columns = [
        {
            name: '',
            field: 'checked',
            type: 'checkbox',
            shown: true,
            checked: true,
            totalRow: true,
            unselectable: true,
            order: false,
            disabled: false
        },
        {
            name: 'Domain',
            field: 'domain',
            unselectable: true,
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
            name: 'Exchange',
            field: 'exchange',
            unselectable: true,
            checked: true,
            type: 'clickPermissionOrText',
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'An exchange where your content is being promoted..',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            shown: true,
            help: "Amount spent per media source.",
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
        }/*,
        {
            name: '',
            nameCssClass: 'data-status-icon',
            type: 'dataStatus',
            internal: $scope.isPermissionInternal('zemauth.data_status_column'),
            shown: $scope.hasPermission('zemauth.data_status_column'),
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'Status of third party data accuracy.',
            disabled: false
        },*/
    ];

    $scope.initColumns = function () {
        var cols;

        cols = zemCustomTableColsService.load('adGroupPublishers', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('adGroupPublishers', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.loadRequestInProgress = false;

    $scope.orderTableData = function(order) {
        $scope.order = order;
        getTableData();
    };

    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.adGroupPublishersTable.get($state.params.id, $scope.pagination.currentPage, $scope.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {

                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.totals.checked = $scope.selectedTotals;
                $scope.notifications = data.notifications;
                $scope.lastChange = data.lastChange;
                $scope.dataStatus = data.dataStatus;
                $scope.pagination = data.pagination;

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

        if (values.indexOf($scope.chartMetric1) === -1) {
            $scope.chartMetric1 = constants.chartMetric.CLICKS;
        }

        if ($scope.chartMetric2 !== 'none' && values.indexOf($scope.chartMetric2) === -1) {
            $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
        }

        return [$scope.chartMetric1, $scope.chartMetric2];
    };

    var setChartOptions = function (goals) {
        $scope.chartMetricOptions = options.adGroupChartMetrics;
    };

    var getDailyStats = function () {
        $scope.selectedPublisherIds = []
        $scope.selectedTotals = true
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

    $scope.init = function() {
        var data = $scope.adGroupData[$state.params.id];
        var sourceIds = $location.search().source_ids || (data && data.sourceIds && data.sourceIds.join(','));
        var sourceTotals = $location.search().source_totals || (data && data.sourceTotals ? 1 : null);


        var page = parseInt($location.search().page)
        if (isNaN(page)) {
            page = data && data.page;
        }
        var size = parseInt($location.search().size || '0'); 


        userSettings.register('chartMetric1');
        userSettings.register('chartMetric2');
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
        $scope.initColumns();

        getTableData();
        getDailyStats();
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


    var updateTableData = function (rowsUpdates, totalsUpdates) {
        $scope.rows.forEach(function (row) {
            var rowUpdates = rowsUpdates[row.id];
            if (rowUpdates) {
                updateObject(row, rowUpdates);
            }
        });

        updateObject($scope.totals, totalsUpdates);
    };

    var updateObject = function (object, updates) {
        for (var key in updates) {
            if (updates.hasOwnProperty(key)) {
                object[key] = updates[key];
            }
        }
    };

    $scope.$on('$destroy', function () {
        $timeout.cancel($scope.lastChangeTimeout);
    });

    $scope.init();
}]);
