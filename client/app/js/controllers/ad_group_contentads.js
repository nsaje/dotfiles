/*globals oneApp,moment,constants,options*/
oneApp.controller('AdGroupAdsCtrl', ['$scope', '$state', '$location', '$window', '$timeout', 'api', 'zemCustomTableColsService', 'localStorageService', 'zemChartService', function ($scope, $state, $location, $window, $timeout, api, zemCustomTableColsService, localStorageService, zemChartService) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.order = '-cost';
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.sourceChartMetric.CLICKS;
    $scope.chartMetric2 = constants.sourceChartMetric.IMPRESSIONS;
    $scope.dailyStats = [];
    $scope.chartData = undefined;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.sourceChartMetrics = options.sourceChartMetrics;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.pagination = {
        currentPage: 1,
    };
    $scope.columns = [
        {
            name: 'URL',
            field: 'url',
            checked: true,
            type: 'url',
            help: 'The web address of the content ad.'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            help: "The amount spent per creative."
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            help: "The average CPC for each content ad."
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
            help: 'The number of times a content ad has been clicked.'
        },
        {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number',
            help: 'The number of times a content ad has been displayed.'

        },
        {
            name: 'CTR',
            field: 'ctr',
            checked: true,
            type: 'percent',
            help: 'The number of clicks divided by the number of impressions.'
        },
        {
            name: 'Visits',
            field: 'visits',
            checked: true,
            type: 'number',
            help: 'The number of visits as reported by Google Analytics.'
        },
        {
            name: 'Pageviews',
            field: 'pageviews',
            checked: true,
            type: 'number',
            help: 'The number of pageviews as reported by Google Analytics.'
        },
        {
            name: 'New Users',
            field: 'percent_new_users',
            checked: false,
            type: 'percent',
            help: 'Percentage of visits made by new users, as reported by Google Analytics.'
        },
        {
            name: 'Bounce Rate',
            field: 'bounce_rate',
            checked: false,
            type: 'percent',
            help: 'Bounce rate help goes here.'
        },
        {
            name: 'PV/Visit',
            field: 'pv_per_visit',
            checked: false,
            type: 'number',
            help: 'Help, pageviews per visit.'
        },
        {
            name: 'Avg. ToS',
            field: 'avg_tos',
            checked: false,
            type: 'number',
            help: 'Help, average time on site.'
        },
        {
            name: 'Click Discrepancy',
            field: 'click_discrepancy',
            checked: false,
            type: 'number',
            help: 'number of clicks minus number of visits.'
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

    $scope.setChartData = function () {
        var result = {};

        result.formats = [$scope.chartMetric1, $scope.chartMetric2].map(function (x) {
            var format = null;
            if (x === constants.sourceChartMetric.COST ||
                x === constants.sourceChartMetric.CPC) {
                format = 'currency';
            } else if (x === constants.sourceChartMetric.CTR) {
                format = 'percent';
            } else {
                // check goal metrics for format info
                $scope.sourceChartMetrics.forEach(function (metric) {
                    if (x === metric.value && metric.format) {
                        format = metric.format;
                    }
                });
            }

            return format;
        });

        var data = [[]];
        var lastDate = null;
        var oneDayMs = 24*60*60*1000;
        $scope.dailyStats.forEach(function (stat) {
            // insert nulls for missing values
            if (lastDate) {
                for (var date = lastDate; date < stat.date - oneDayMs; date += oneDayMs) {
                    data[0].push([date, null]);

                    if (data[1]) {
                        data[1].push([date, null]);
                    }
                }
            }
            lastDate = stat.date;

            data[0].push([stat.date, stat[$scope.chartMetric1]]);

            if ($scope.chartMetric2 && $scope.chartMetric2 !== $scope.chartMetric1) {
                if (!data[1]) {
                    data[1] = [];
                }
                data[1].push([stat.date, stat[$scope.chartMetric2]]);
            }
        });

        result.ids = [null];
        result.names = [null];
        result.data = [data];

        $scope.chartData = result;
    };

    $scope.loadRequestInProgress = false;

    $scope.addGoalColumns = function(rows) {
        var alreadyAdded = function(field) {
            for(var i = 0; i < $scope.columns.length; i++) {
                if(field == $scope.columns[i]['field']){
                    return true;
                }
            }
            return false;
        };

        for(var i = 0; i < rows.length; i++) {
            for(var field in rows[i]) {
                if(alreadyAdded(field)) {
                    continue;
                }

                if(field.indexOf(': Conversions') != -1) {
                    var col_descr = {
                        'name': field.substr('goal__'.length),
                        'field': field,
                        'checked': false,
                        'type': 'number',
                        'help': 'Number of goal completions'
                    }
                    $scope.columns.splice($scope.columns.length - 1, 0, col_descr);
                } else if(field.indexOf(': Conversion Rate') != -1) {
                    var col_descr = {
                        'name': field.substr('goal__'.length),
                        'field': field,
                        'checked': false,
                        'type': 'percent',
                        'help': 'Conversion rate help'
                    }
                    $scope.columns.splice($scope.columns.length - 1, 0, col_descr);
                }
            }
        }
    };

    $scope.getTableData = function () {
        $scope.loadRequestInProgress = true;

        api.adGroupAdsTable.get($state.params.id, $scope.pagination.currentPage, $scope.pagination.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.addGoalColumns(data.rows);

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

    $scope.orderTableData = function(field) {
        // Title and URL are sorted ascending by default while everything else
        // is descending.
        if (field === 'title' || field === 'url') {
            if ($scope.order === field) {
                $scope.order = '-' + field;
            } else {
                $scope.order = field;
            }
        } else {
            if ($scope.order === '-' + field) {
                $scope.order = field;
            } else {
                $scope.order = '-' + field;
            }
        }

        $location.search('order', $scope.order);
        localStorageService.set('adGroupContentAds.order', $scope.order);
        $scope.getTableData();
    };

    $scope.getDailyStats = function () {
        api.adGroupDailyStats.list($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, null, true).then(
            function (data) {
                $scope.dailyStats = data.stats;
                $scope.sourceChartMetrics = options.sourceChartMetrics.concat(data.options);
                $scope.setChartData();
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

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.setChartData();
            $location.search('chart_metric1', $scope.chartMetric1);
            localStorageService.set('adGroupContentAds.chartMetric1', $scope.chartMetric1);
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.setChartData();
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
        var chartChanged = false;

        var data = $scope.adGroupData[$state.params.id];
        var page = $location.search().page || (data && data.page);

        if (chartMetric1 !== undefined && $scope.chartMetric1 !== chartMetric1) {
            $scope.chartMetric1 = chartMetric1;
            $location.search('chart_metric1', chartMetric1);
            chartChanged = true;
        }

        if (chartMetric2 !== undefined && $scope.chartMetric2 !== chartMetric2) {
            $scope.chartMetric2 = chartMetric2;
            $location.search('chart_metric2', chartMetric2);
            chartChanged = true;
        }

        if (chartHidden) {
            $scope.isChartShown = false;
        }

        if (chartChanged) {
            $scope.setChartData();
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
