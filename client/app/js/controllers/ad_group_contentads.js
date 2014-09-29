/*globals oneApp,moment,constants,options*/
oneApp.controller('AdGroupAdsCtrl', ['$scope', '$state', '$location', '$window', '$timeout', 'api', 'zemCustomTableColsService', 'zemPostclickMetricsService', 'localStorageService', 'zemChartService', '$compile', function ($scope, $state, $location, $window, $timeout, api, zemCustomTableColsService, zemPostclickMetricsService, localStorageService, zemChartService, $compile) {
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
    $scope.incompletePostclickMetrics = false;
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
            extraTdCss: 'trimmed title',
            titleField: 'title',
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
            titleField: 'url',
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

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
               'url_link', 'cost', 'cpc', 'clicks', 'impressions', 'ctr'
            ]
        },
        {
            'name': 'Audience Metrics',
            'fields': [
                'visits', 'pageviews', 'percent_new_users',
                'bounce_rate', 'pv_per_visit', 'avg_tos', 
                'click_discrepancy'
            ]
        }
    ];

    var initColumns = function () {
        var cols;

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            zemPostclickMetricsService.insertColumns($scope.columns, $scope.isPermissionInternal('zemauth.postclick_metrics'));
        }

        cols = zemCustomTableColsService.load('adGroupAdsCols', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('adGroupAdsCols', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.exportSelect2Config = {
        minimumResultsForSearch: -1,
        formatResult: function (object) {
            if (!object.disabled) {
                return angular.element(document.createElement('span')).text(object.text);
            }

            var popoverEl = angular.element(document.createElement('div'));

            popoverEl.attr('popover', 'There is too much data to export. Please choose a smaller date range.');
            popoverEl.attr('popover-trigger', 'mouseenter');
            popoverEl.attr('popover-append-to-body', 'true');
            popoverEl.text(object.text);

            return $compile(popoverEl)($scope);
        },
        sortResults: function (results) {
            // used to set disabled property on results
            var numDays = $scope.dateRange.endDate.diff($scope.dateRange.startDate, 'days');

            return results.map(function (result) {
                if (result.id === 'excel' && ($scope.pagination.count * numDays) > 7000) {
                    result.disabled = true;
                }
                return result;
            });
        }
    };

    $scope.$watch('isChartShown', function (newValue, oldValue) {
        zemChartService.save('zemChart', newValue);
    });

    $scope.loadRequestInProgress = false;

    var getTableData = function () {
        $scope.loadRequestInProgress = true;

        api.adGroupAdsTable.get($state.params.id, $scope.pagination.currentPage, $scope.pagination.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.incompletePostclickMetrics = data.incomplete_postclick_metrics;

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
        getTableData();
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

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.postclick_metrics')
            );
        }
    };

    var getDailyStats = function () {
        api.dailyStats.list('ad_groups', $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, null, true, getDailyStatsMetrics()).then(
            function (data) {
                setChartOptions();
                $scope.chartData = data.chartData;
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
            getDailyStats();
            $location.search('chart_metric1', $scope.chartMetric1);
            localStorageService.set('adGroupContentAds.chartMetric1', $scope.chartMetric1);
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            getDailyStats();
            $location.search('chart_metric2', $scope.chartMetric2);
            localStorageService.set('adGroupContentAds.chartMetric2', $scope.chartMetric2);
        }
    });

    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if(newValue === true && oldValue === false){
            pollSyncStatus();
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
        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get('adGroupContentAds.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get('adGroupContentAds.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;
        var size = $location.search().size || localStorageService.get('adGroupContentAds.paginationSize') || $scope.sizeRange[0];
        var order = $location.search().order || localStorageService.get('adGroupContentAds.order') || $scope.order;

        var data = $scope.adGroupData[$state.params.id];
        var page = $location.search().page || (data && data.page);

        setChartOptions();

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
        }

        if (size !== undefined && $scope.pagination.size !== size) {
            $scope.pagination.size = size;
        }
        
        if (order !== undefined && $scope.order !== order) {
            $scope.order = order;
            $location.search('order', order);
        }

        $scope.loadPage();
        getDailyStats();
        initColumns();
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

            getTableData();
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
