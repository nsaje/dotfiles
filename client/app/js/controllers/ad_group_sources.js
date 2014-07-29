/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupSourcesCtrl', ['$scope', '$state', '$location', '$window', '$timeout', 'api', 'zemCustomTableColsService', 'zemChartService', function ($scope, $state, $location, $window, $timeout, api, zemCustomTableColsService, zemChartService) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.triggerSyncFailed = false;
    $scope.selectedSourceIds = [];
    $scope.selectedSourceTotals = true;
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.sourceChartMetric.CLICKS;
    $scope.chartMetric2 = constants.sourceChartMetric.IMPRESSIONS;
    $scope.dailyStats = [];
    $scope.chartData = undefined;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-clicks';
    $scope.columns = [
        {
            name: 'Bid CPC',
            field: 'bid_cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3
        },
        {
            name: 'Daily Budget',
            field: 'daily_budget',
            checked: true,
            type: 'currency'
        },
        {
            name: 'Cost',
            field: 'cost',
            checked: true,
            type: 'currency'
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number'
        },
        {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number'
        },
        {
            name: 'CTR',
            field: 'ctr',
            checked: true,
            type: 'percent'
        },
        {
            name: 'Last OK Sync',
            field: 'last_sync',
            checked: false,
            type: 'datetime'
        }
    ];

    var cols = zemCustomTableColsService.load('adGroupSourcesCols', $scope.columns);
    $scope.selectedColumnsCount = cols.length;

    $scope.$watch('columns', function (newValue, oldValue) {
        cols = zemCustomTableColsService.save('adGroupSourcesCols', newValue);
        $scope.selectedColumnsCount = cols.length;
    }, true);

    $scope.$watch('isChartShown', function (newValue, oldValue) {
        zemChartService.save('zemChart', newValue);
    });

    $scope.setChartData = function () {
        var result = {
            formats: [],
            data: [],
            names: [],
            ids: []
        };

        result.formats = [$scope.chartMetric1, $scope.chartMetric2].map(function (x) {
            var format = null;
            if (x === constants.sourceChartMetric.COST ||
                x === constants.sourceChartMetric.CPC) {
                format = 'currency';
            } else if (x === constants.sourceChartMetric.CTR) {
                format = 'percent';
            }

            return format;
        });

        var temp = {};
        $scope.dailyStats.forEach(function (stat) {
            if (!temp.hasOwnProperty(stat.sourceId)) {
                temp[stat.sourceId] = {
                    name: stat.sourceName,
                    id: stat.sourceId,
                    data: [[]]
                };
            }

            temp[stat.sourceId].data[0].push([stat.date, stat[$scope.chartMetric1]]);

            if ($scope.chartMetric2 && $scope.chartMetric2 !== $scope.chartMetric1) {
                if (!temp[stat.sourceId].data[1]) {
                    temp[stat.sourceId].data[1] = [];
                }
                temp[stat.sourceId].data[1].push([stat.date, stat[$scope.chartMetric2]]);
            }
        });

        Object.keys(temp).forEach(function (sourceId) {
            result.data.push(temp[sourceId].data);
            result.names.push(temp[sourceId].name),
            result.ids.push(temp[sourceId].id);
        });

        $scope.chartData = result;
    };

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
        $scope.getTableData();
    };

    $scope.getAdGroupState = function() {
        api.adGroupSettings.get($state.params.id).then(
            function(data) {
                $scope.setAdGroupPaused(data.settings.state === 2);
            },
            function(){
                // error
            }
        );
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

    $scope.getDailyStats = function () {
        api.adGroupSourcesDailyStats.list($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedSourceIds, $scope.selectedSourceTotals).then(
            function (data) {
                $scope.dailyStats = data;
                $scope.setChartData();
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
        if (sourceId) {
            $scope.updateSelectedSources(String(sourceId));
        } else {
            $scope.selectedSourceTotals = false;
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
        if (!$scope.selectedSourceTotals && !$scope.selectedSourceIds.length) {
            $scope.selectedSourceTotals = true;
        }

        $location.search('source_ids', $scope.selectedSourceIds.join(','));
        $location.search('source_totals', $scope.selectedSourceTotals ? 1 : null);

        $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);
        $scope.setAdGroupData('sourceTotals', $scope.selectedSourceTotals);

        $scope.getDailyStats();
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
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.setChartData();
            $location.search('chart_metric2', $scope.chartMetric2);
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
        var chartMetric1 = $location.search().chart_metric1;
        var chartMetric2 = $location.search().chart_metric2;
        var chartHidden = $location.search().chart_hidden;
        var changed = false;

        if (chartMetric1 !== undefined && $scope.chartMetric1 !== chartMetric1) {
            $scope.chartMetric1 = chartMetric1;
            changed = true;
        }

        if (chartMetric2 !== undefined && $scope.chartMetric2 !== chartMetric2) {
            $scope.chartMetric2 = chartMetric2;
            changed = true;
        }

        if (chartHidden) {
            $scope.isChartShown = false;
        }

        if (changed) {
            $scope.setChartData();
        }

        // selected rows
        var sourceIds = $location.search().source_ids;
        var sourceTotals = !!$location.search().source_totals;

        if (sourceIds) {
            $scope.selectedSourceIds = sourceIds.split(',');
            $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);

            if ($scope.rows) {
                $scope.selectSources();
            }
        }


        $scope.order = $location.search().order || $scope.order;
        $scope.selectedSourceTotals = !$scope.selectedSourceIds.length || sourceTotals;
        $scope.setAdGroupData('sourceTotals', $scope.selectedSourceTotals);

        $scope.getAdGroupState();
    };

    // export
    $scope.downloadReport = function() {
        $window.open('api/ad_groups/' + $state.params.id + '/sources/export/?type=' + $scope.exportType + '&start_date=' + $scope.dateRange.startDate.format() + '&end_date=' + $scope.dateRange.endDate.format(), '_blank');
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
                        $scope.triggerSyncFailed = true;
                        $scope.isSyncInProgress = false;
                    }
                ).finally(function() {
                    pollSyncStatus();
                });
            }, 1000);
        }
    }

    pollSyncStatus();

    // trigger sync
    $scope.triggerSync = function() {
        api.adGroupSync.get($state.params.id).then(
            function () {
                $scope.isSyncInProgress = true;
            },
            function () {
                // error
                $scope.triggerSyncFailed = true;
            }
        );
    }

    $scope.init();
}]);
