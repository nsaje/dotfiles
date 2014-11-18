/*globals oneApp,moment,constants,options*/
oneApp.controller('MediaSourcesCtrl', ['$scope', '$state', 'zemChartService', '$location', 'localStorageService', 'api', 'zemPostclickMetricsService', 'zemCustomTableColsService', '$timeout', function ($scope, $state, zemChartService, $location, localStorageService, api, zemPostclickMetricsService, zemCustomTableColsService, $timeout) {
    $scope.localStoragePrefix = null;
    $scope.selectedTotals = true;
    $scope.selectedSourceIds = [];
    $scope.chartMetrics = [];
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.chartMetricOptions = [];
    $scope.chartBtnTitle = 'Hide chart';

    $scope.order = '-cost';
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.isIncompletePostclickMetrics = false;
    $scope.sources = [];

    $scope.updateSelectedSources = function (sourceId) {
        var i = $scope.selectedSourceIds.indexOf(sourceId);

        if (i > -1) {
            $scope.selectedSourceIds.splice(i, 1);
        } else {
            $scope.selectedSourceIds.push(sourceId);
        }

        $scope.columns[0].disabled = $scope.selectedSourceIds.length >= 4;
    };

    $scope.selectedSourcesChanged = function (row, checked) {
        if (row.id) {
            $scope.updateSelectedSources(row.id);
        } else {
            $scope.selectedTotals = !$scope.selectedTotals;
        }

        $scope.updateSelectedRowsData();
    };

    $scope.updateSelectedRowsData = function () {
        if (!$scope.selectedTotals && !$scope.selectedSourceIds.length) {
            $scope.selectedTotals = true;
            $scope.totals.checked = true;
        }

        $location.search('source_ids', $scope.selectedSourceIds.join(','));
        $location.search('source_totals', $scope.selectedTotals ? 1 : null);

        getDailyStats();
    };

    $scope.selectRows = function () {
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selectedSourceIds.indexOf(x.id) > -1;
        });
    };

    $scope.selectedSourceRemoved = function (sourceId) {
        if (sourceId !== 'totals') {
            $scope.updateSelectedSources(String(sourceId));
        } else {
            $scope.selectedTotals = false;
            $scope.totals.checked = false;
        }

        $scope.selectRows();
        $scope.updateSelectedRowsData();
    };

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
            selectCallback: $scope.selectedSourcesChanged,
            disabled: false
        },
        {
            name: 'Media Source',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'text',
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'A media source where your content is being promoted.',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'Status',
            field: 'status',
            unselectable: true,
            checked: true,
            type: 'text',
            shown: true,
            totalRow: false,
            help: 'Status of a particular media source (enabled or paused).',
            order: true,
            orderField: 'status',
            initialOrder: 'asc'
        },
        {
            name: 'Min Bid',
            field: 'min_bid_cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'Minimum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Max Bid',
            field: 'max_bid_cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Daily Budget',
            field: 'daily_budget',
            checked: true,
            type: 'currency',
            shown: true,
            help: 'Maximum budget per day.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Yesterday Spend',
            field: 'yesterday_cost',
            checked: false,
            type: 'currency',
            help: 'Amount that you have spent yesterday for promotion on specific media source.',
            internal: $scope.isPermissionInternal('reports.yesterday_spend_view'),
            shown: $scope.hasPermission('reports.yesterday_spend_view'),
            totalRow: true,
            order: true,
            initialOrder: 'desc'
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
        },
        {
            name: 'Last OK Sync (EST)',
            field: 'last_sync',
            checked: false,
            type: 'datetime',
            shown: true,
            help: 'Dashboard reporting data is synchronized on an hourly basis. This is when the most recent synchronization occurred (in Eastern Standard Time).',
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        }
    ];

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
               'min_bid_cpc', 'max_bid_cpc', 'daily_budget', 'cost', 
               'cpc', 'clicks', 'impressions', 'ctr', 'yesterday_cost'
            ]
        },
        {
            'name': 'Audience Metrics',
            'fields': [
                'visits', 'pageviews', 'percent_new_users',
                'bounce_rate', 'pv_per_visit', 'avg_tos', 
                'click_discrepancy'
            ]
        },
        {
            'name': 'Data Sync',
            'fields': ['last_sync']
        }
    ];

    $scope.initColumns = function () {
        var cols;

        zemPostclickMetricsService.insertColumns($scope.columns, $scope.hasPermission('zemauth.postclick_metrics'), $scope.isPermissionInternal('zemauth.postclick_metrics'));

        cols = zemCustomTableColsService.load($scope.localStoragePrefix + 'Cols', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save($scope.localStoragePrefix + 'Cols', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $location.search('chart_metric1', $scope.chartMetric1);

            if (!hasMetricData($scope.chartMetric1)) {
                localStorageService.set($scope.localStoragePrefix + '.chartMetric1', $scope.chartMetric1);
                getDailyStats();
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
                localStorageService.set($scope.localStoragePrefix + '.chartMetric2', $scope.chartMetric2);
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    $scope.toggleChart = function () {
        $scope.isChartShown = !$scope.isChartShown;
        $scope.chartBtnTitle = $scope.isChartShown ? 'Hide chart' : 'Show chart';
        $location.search('chart_hidden', !$scope.isChartShown ? '1' : null);

        $timeout(function() {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    $scope.$watch('isChartShown', function (newValue, oldValue) {
        zemChartService.save('zemChart', newValue);
    });

    var hasMetricData = function (metric) {
        var hasData = false;
        $scope.chartData.forEach(function (group) {
            if (group.seriesData[metric] !== undefined) {
                hasData = true;
            }
        });

        return hasData;
    };

    var getDailyStatsMetrics = function () {
        var metrics = [$scope.chartMetric1, $scope.chartMetric2];

        var values = $scope.chartMetrics.map(function (option) {
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

    $scope.orderTableData = function(order) {
        $scope.order = order;

        $location.search('order', $scope.order);
        localStorageService.set($scope.localStoragePrefix + '.order', $scope.order);
        getTableData();
    };


    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.sourcesTable.get($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.totals.checked = $scope.selectedTotals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.selectRows();
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };

    var getDailyStats = function () {
        api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedSourceIds, $scope.selectedTotals, getDailyStatsMetrics(), true).then(
            function (data) {
                setChartOptions();
            
                // Select default metrics if selected metrics are not defined
                var values = $scope.chartMetricOptions.map(function (option) {
                    return option.value;
                });

                if (values.indexOf($scope.chartMetric1) === -1) {
                    $scope.chartMetric1 = constants.chartMetric.CLICKS;
                }
                if (values.indexOf($scope.chartMetric2) === -1 && $scope.chartMetric2 !== 'none') {
                    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
                }

                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    var setChartOptions = function () {
        $scope.chartMetricOptions = $scope.chartMetrics;

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.chartMetricOptions = $scope.chartMetricOptions.concat(options.adGroupChartPostClickMetrics.map(function (option) {
                if ($scope.isPermissionInternal('zemauth.postclick_metrics')) {
                    option.internal = true;
                }

                return option;
            }));
        }
    };

    var init = function () {
        if ($scope.level === constants.level.ALL_ACCOUNTS) {
            $scope.localStoragePrefix = 'allAccountSources';
            $scope.chartMetrics = options.allAccountsChartMetrics;
        } else if ($scope.level === constants.level.ACCOUNTS) {
            $scope.localStoragePrefix = 'accountSources';
            $scope.chartMetrics = options.accountChartMetrics;
        } else if ($scope.level === constants.level.CAMPAIGNS) {
            $scope.localStoragePrefix = 'campaignSources';
            $scope.chartMetrics = options.campaignChartMetrics;
        }

        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get($scope.localStoragePrefix + '.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get($scope.localStoragePrefix + '.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;

        var sourceIds = $location.search().source_ids;
        var sourceTotals = $location.search().source_totals;

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

        if (sourceIds) {
            $scope.selectedSourceIds = sourceIds.split(',');
            $location.search('source_ids', sourceIds);
        }

        $scope.selectedTotals = !$scope.selectedSourceIds.length || !!sourceTotals;
        $location.search('source_totals', sourceTotals);

        $scope.initColumns();

        getDailyStats();
        getTableData();
        pollSyncStatus();
    };

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

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('source_ids', null);
        $location.search('source_totals', null);
        $location.search('chart_metric1', null);
        $location.search('chart_metric2', null);
    });

    var pollSyncStatus = function() {
        if($scope.isSyncInProgress){
            $timeout(function() {
                var promise = null;

                if ($scope.level === constants.level.ALL_ACCOUNTS) {
                    promise = api.checkAccountsSyncProgress.get();
                } else if ($scope.level === constants.level.ACCOUNTS) {
                    promise = api.checkCampaignSyncProgress.get(undefined, $state.params.id);
                } else if ($scope.level === constants.level.CAMPAIGNS) {
                    promise = api.checkCampaignSyncProgress.get($state.params.id);
                }

                promise.then(
                    function(data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if($scope.isSyncInProgress === false){
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
    };

    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;

        if ($scope.level === constants.level.ALL_ACCOUNTS) {
            api.accountSync.get();
        } else if ($scope.level === constants.level.ACCOUNTS) {
            api.accountSync.get($state.params.id);
        } else if ($scope.level === constants.level.CAMPAIGNS) {
            api.campaignSync.get($state.params.id);
        }
    };

    init();
}]);
