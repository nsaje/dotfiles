/*globals oneApp,moment,constants,options*/
oneApp.controller('AdGroupAdsCtrl', ['$scope', '$state', '$location', '$window', '$timeout', 'api', 'zemCustomTableColsService', 'localStorageService', 'zemChartService', function ($scope, $state, $location, $window, $timeout, api, zemCustomTableColsService, localStorageService, zemChartService) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.order = '-cost';
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.chartMetricOptions = options.adGroupChartMetrics;
    $scope.chartGoalMetrics = null;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.pagination = {
        currentPage: 1,
    };
    $scope.columns = [
        {
            name: 'Title',
            field: 'title_link',
            unselectable: true,
            checked: true,
            type: 'linkText',
            hasTotalsLabel: true,
            totalRow: false,
            help: 'The creative title/headline of a content ad.',
            extraTdCss: 'trimmed',
            order: true,
            orderField: 'title',
            initialOrder: 'asc'
        },
        {
            name: 'URL',
            field: 'url_link',
            checked: true,
            type: 'linkText',
            help: 'The web address of the content ad.',
            extraTdCss: 'trimmed url',
            totalRow: false,
            order: true,
            orderField: 'url',
            initialOrder: 'asc'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            help: "The amount spent per creative.",
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            help: "The average CPC for each content ad.",
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
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
            help: 'The number of clicks divided by the number of impressions.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }
    ];

    var cols = zemCustomTableColsService.load('adGroupAdsCols', $scope.columns);
    $scope.selectedColumnsCount = cols.length;

    $scope.$watch('columns', function (newValue, oldValue) {
        cols = zemCustomTableColsService.save('adGroupAdsCols', newValue);
        $scope.selectedColumnsCount = cols.length;
    }, true);

    $scope.$watch('isChartShown', function (newValue, oldValue) {
        zemChartService.save('zemChart', newValue);
    });

    $scope.loadRequestInProgress = false;

    $scope.getTableData = function () {
        $scope.loadRequestInProgress = true;

        api.adGroupAdsTable.get($state.params.id, $scope.pagination.currentPage, $scope.pagination.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.incompleteTrafficMetrics = data.incomplete_traffic_metrics;
                $scope.incompletePostclickMetrics = data.incomplete_postclick_metrics;
                $scope.incompleteConversionMetrics = data.incomplete_conversion_metrics;

                $scope.order = data.order;
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

    $scope.orderTableData = function(order) {
        $scope.order = order;

        $location.search('order', $scope.order);
        localStorageService.set('adGroupContentAds.order', $scope.order);
        $scope.getTableData();
    };

    var getDailyStatsMetrics = function () {
        var metrics = [$scope.chartMetric1, $scope.chartMetric2];

        var values = options.adGroupChartMetrics.map(function (option) {
            return option.value;
        });

        if (values.indexOf($scope.chartMetric1) === -1) {
            metrics.push(constants.chartMetric.CLICKS);
        }

        if (values.indexOf($scope.chartMetric2) === -1) {
            metrics.push(constants.chartMetric.IMPRESSIONS);
        }

        return metrics;
    };

    $scope.getDailyStats = function () {
        api.dailyStats.list('ad_groups', $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, null, true, getDailyStatsMetrics()).then(
            function (data) {
                // Select default metrics if selected metrics are not defined
                var values = $scope.chartMetricOptions.map(function (option) {
                    return option.value;
                });

                if (values.indexOf($scope.chartMetric1) === -1) {
                    $scope.chartMetric1 = constants.chartMetric.CLICKS;
                }
                if (values.indexOf($scope.chartMetric2) === -1) {
                    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
                }

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
        $scope.isChartShown = !$scope.isChartShown;
        $scope.chartBtnTitle = $scope.isChartShown ? 'Hide chart' : 'Show chart';
        $location.search('chart_hidden', !$scope.isChartShown ? '1' : null);
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
            $location.search('chart_metric1', $scope.chartMetric1);

            if (!hasMetricData($scope.chartMetric1)) {
                localStorageService.set('adGroupContentAds.chartMetric1', $scope.chartMetric1);
                $scope.getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $location.search('chart_metric2', $scope.chartMetric2);

            if (!hasMetricData($scope.chartMetric2)) {
                localStorageService.set('adGroupContentAds.chartMetric2', $scope.chartMetric2);
                $scope.getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if(newValue === true && oldValue === false){
            pollSyncStatus();
        }
    });

    // From parent scope (mainCtrl).
    $scope.$watch('dateRange', function (newValue, oldValue) {
        $scope.getDailyStats();
        $scope.getTableData();
    });

    $scope.init = function() {
        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get('adGroupContentAds.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get('adGroupContentAds.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;
        var size = $location.search().size || localStorageService.get('adGroupContentAds.paginationSize') || $scope.sizeRange[0];
        var order = $location.search().order || localStorageService.get('adGroupContentAds.order') || $scope.order;
        var tableChanged = false;

        var data = $scope.adGroupData[$state.params.id];
        var page = $location.search().page || (data && data.page);

        if (chartMetric1 !== undefined && $scope.chartMetric1 !== chartMetric1) {
            $scope.chartMetric1 = chartMetric1;
            $location.search('chart_metric1', chartMetric1);
        }

        if (chartMetric2 !== undefined && $scope.chartMetric2 !== chartMetric2) {
            $scope.chartMetric2 = chartMetric2;
            $location.search('chart_metric2', chartMetric2);
        }

        if (chartHidden) {
            $scope.isChartShown = false;
        }

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
            $scope.setAdGroupData('page', page);
            $location.search('page', page);
            tableChanged = true;
        }

        if (size !== undefined && $scope.pagination.size !== size) {
            $scope.pagination.size = size;
            tableChanged = true;
        }
        
        if (order !== undefined && $scope.order !== order) {
            $scope.order = order;
            $location.search('order', order);
            tableChanged = true;
        }

        if (tableChanged) {
            $scope.loadPage();
        }

    };
    
    // pagination
    $scope.sizeRange = [5, 10, 20, 50];

    $scope.loadPage = function(page) {
        if(page && page > 0 && page <= $scope.pagination.numPages) {
            $scope.pagination.currentPage = page;
        }

        if ($scope.pagination.currentPage && $scope.pagination.size) {
            $location.search('page', $scope.pagination.currentPage);
            $scope.setAdGroupData('page', $scope.pagination.currentPage);

            $scope.getTableData();
            $scope.getAdGroupState();
        }
    };

    $scope.changePaginationSize = function() {
        // Here we use additional scope variable pagination.sizeTemp
        // to allow repeated selection of already selected options
        $scope.pagination.size = $scope.pagination.sizeTemp;
        $scope.pagination.sizeTemp = '';

        $location.search('size', $scope.pagination.size);
        localStorageService.set('adGroupContentAds.paginationSize', $scope.pagination.size);
        $scope.loadPage();
    };

    // export
    $scope.downloadReport = function() {
        $window.open('api/ad_groups/' + $state.params.id + '/contentads/export/?type=' + $scope.exportType + '&start_date=' + $scope.dateRange.startDate.format() + '&end_date=' + $scope.dateRange.endDate.format(), '_blank');
        $scope.exportType = '';
    };

    
    var pollSyncStatus = function() {
        if($scope.isSyncInProgress){
            $timeout(function() {
                api.checkSyncProgress.get($state.params.id).then(
                    function(data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if($scope.isSyncInProgress == false){
                            // we found out that the sync is no longer in progress
                            // time to reload the data
                            $scope.getTableData();
                            $scope.getDailyStats();
                        }
                    },
                    function(data) {
                        // error
                        $scope.isSyncInProgress = false;
                    }
                ).finally(function() {
                    pollSyncStatus();
                });
            }, 5000);
        }
    }

    pollSyncStatus();

    // trigger sync
    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;
        api.adGroupSync.get($state.params.id);
    }

    $scope.init();
}]);
