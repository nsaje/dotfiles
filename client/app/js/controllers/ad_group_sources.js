/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupSourcesCtrl', ['$scope', '$state', '$location', '$window', '$timeout', 'api', 'zemCustomTableColsService', 'zemChartService', 'localStorageService', function ($scope, $state, $location, $window, $timeout, api, zemCustomTableColsService, zemChartService, localStorageService) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.selectedSourceIds = [];
    $scope.selectedTotals = true;
    $scope.constants = constants;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.chartMetricOptions = options.adGroupChartMetrics;
    $scope.chartGoalMetrics = null;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-cost';
    $scope.sources = [];
    $scope.sourcesWaiting = null;
    $scope.columns = [
        {
            name: 'Bid CPC',
            field: 'bid_cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.'
        },
        {
            name: 'Daily Budget',
            field: 'daily_budget',
            checked: true,
            type: 'currency',
            help: 'Maximum budget per day.'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            help: "Amount spent per media source."
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            help: "The average CPC."
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
            name: 'Last OK Sync',
            field: 'last_sync',
            checked: false,
            type: 'datetime',
            help: 'Dashboard reporting data is synchronized on an hourly basis. This is when the most recent synchronization occurred.'
        }
    ];

    $scope.initColumns = function () {
        var cols;

        if ($scope.hasPermission('reports.yesterday_spend_view')) {
            $scope.columns.splice(2, 0, {
                name: 'Yesterday Spend',
                field: 'yesterday_cost',
                checked: false,
                type: 'currency',
                help: 'Amount that you have spent yesterday for promotion on specific media source.',
                internal: $scope.isPermissionInternal('reports.yesterday_spend_view')
            });
        }

        if ($scope.hasPermission('zemauth.supply_dash_link_view')) {
            $scope.columns.splice(0, 0, {
                name: 'Link',
                field: 'supply_dash_url',
                checked: false,
                type: 'link',
                internal: $scope.isPermissionInternal('zemauth.supply_dash_link_view')
            });
        }

        cols = zemCustomTableColsService.load('adGroupSourcesCols', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('adGroupSourcesCols', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.$watch('isChartShown', function (newValue, oldValue) {
        zemChartService.save('zemChart', newValue);
    });

    $scope.loadRequestInProgress = false;

    $scope.orderRows = function (col) {
        if ($scope.order.indexOf(col) === 1) {
            $scope.order = col;
        } else if ($scope.order.indexOf(col) === -1 && col === 'name') {
            $scope.order = col;
        } else {
            $scope.order = '-' + col;
        }

        $location.search('order', $scope.order);
        localStorageService.set('adGroupSources.order', $scope.order);
        $scope.getTableData();
    };

    $scope.getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.adGroupSourcesTable.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.selectSources();
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
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
        api.dailyStats.list('ad_groups', $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedSourceIds, $scope.selectedTotals, getDailyStatsMetrics()).then(
            function (data) {
                $scope.chartMetricOptions = options.adGroupChartMetrics.concat(Object.keys(data.goals).map(function (goalId) {
                    return {
                        name: data.goals[goalId].name,
                        value: goalId
                    }
                }));

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

    $scope.updateSelectedSources = function (sourceId) {
        var i = $scope.selectedSourceIds.indexOf(sourceId);
        if (i > -1) {
            $scope.selectedSourceIds.splice(i, 1);
        } else {
            $scope.selectedSourceIds.push(sourceId);
        }
    };

    $scope.selectedSourceRemoved = function (sourceId) {
        if (sourceId !== 'totals') {
            $scope.updateSelectedSources(String(sourceId));
        } else {
            $scope.selectedTotals = false;
        }

        $scope.selectSources();
        $scope.updateSelectedRowsData();
    };

    $scope.selectedSourcesChanged = function (sourceId) {
        if (sourceId) {
            $scope.updateSelectedSources(sourceId);
        }

        $scope.updateSelectedRowsData();
    };

    $scope.updateSelectedRowsData = function () {
        if (!$scope.selectedTotals && !$scope.selectedSourceIds.length) {
            $scope.selectedTotals = true;
        }

        $location.search('source_ids', $scope.selectedSourceIds.join(','));
        $location.search('source_totals', $scope.selectedTotals ? 1 : null);

        $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);
        $scope.setAdGroupData('sourceTotals', $scope.selectedTotals);

        $scope.getDailyStats();
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
                localStorageService.set('adGroupSources.chartMetric1', $scope.chartMetric1);
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
                localStorageService.set('adGroupSources.chartMetric2', $scope.chartMetric2);
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

    $scope.selectSources = function () {
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selectedSourceIds.indexOf(x.id) > -1;
        });
    };

    $scope.init = function() {
        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get('adGroupSources.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get('adGroupSources.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;
        var order = $location.search().order || localStorageService.get('adGroupSources.order') || $scope.order;

        var data = $scope.adGroupData[$state.params.id];
        var sourceIds = $location.search().source_ids || (data && data.sourceIds && data.sourceIds.join(','));
        var sourceTotals = $location.search().source_totals || (data && data.sourceTotals ? 1 : null);

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
            $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);
            $location.search('source_ids', sourceIds);

            if ($scope.rows) {
                $scope.selectSources();
            }
        }

        if (order !== undefined && $scope.order !== order) {
            $scope.order = order;
            $location.search('order', order);
        }

        $scope.selectedTotals = !$scope.selectedSourceIds.length || !!sourceTotals;
        $scope.setAdGroupData('sourceTotals', $scope.selectedTotals);
        $location.search('source_totals', sourceTotals);

        $scope.getAdGroupState();
        $scope.initColumns();

        $scope.getSources();
    };

    // export
    $scope.downloadReport = function() {
        $window.open('api/ad_groups/' + $state.params.id + '/sources/export/?type=' + $scope.exportType + '&start_date=' + $scope.dateRange.startDate.format() + '&end_date=' + $scope.dateRange.endDate.format(), '_blank');
        $scope.exportType = '';
    };

    $scope.getSources = function () {
        if (!$scope.hasPermission('zemauth.ad_group_sources_add_source')) {
            return;
        }

        api.adGroupSources.get($state.params.id).then(
            function (data) {
                $scope.sources = data.sources;
                $scope.sourcesWaiting = data.sourcesWaiting;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.addSource = function (sourceIdToAdd) {
        if (!sourceIdToAdd) {
            return;
        }

        api.adGroupSources.add($state.params.id, sourceIdToAdd).then(
            function (data) {
                $scope.getSources();
            },
            function (data) {
                // error
                return;
            }
        );

        $scope.sourceIdToAdd = '';
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
