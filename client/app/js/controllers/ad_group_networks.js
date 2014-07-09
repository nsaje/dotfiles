/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupNetworksCtrl', ['$scope', '$state', '$location', '$window', 'api', 'zemCustomTableColsService', function ($scope, $state, $location, $window, api, zemCustomTableColsService) {
    $scope.isSyncRecent = true;
    $scope.selectedNetworkIds = [];
    $scope.selectedNetworkTotals = true;
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.networkChartMetric.CLICKS;
    $scope.chartMetric2 = constants.networkChartMetric.IMPRESSIONS;
    $scope.dailyStats = [];
    $scope.chartData = undefined;
    $scope.isChartShown = true;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.columns = [
        {
            name: 'Bid CPC',
            field: 'bid_cpc',
            checked: true,
            type: 'currency'
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
            name: 'CPC',
            field: 'cpc',
            checked: true,
            type: 'currency'
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
            name: 'Last Sync',
            field: 'last_sync',
            checked: false,
            type: 'datetime'
        }
    ];

    var cols = zemCustomTableColsService.load('adGroupNetworksCols', $scope.columns);
    $scope.selectedColumnsCount = cols.length;

    $scope.$watch('columns', function (newValue, oldValue) {
        cols = zemCustomTableColsService.save('adGroupNetworksCols', newValue);
        $scope.selectedColumnsCount = cols.length;
    }, true);

    $scope.setChartData = function () {
        var result = {
            formats: [],
            data: [[]]
        };
        var i;

        result.formats = [$scope.chartMetric1, $scope.chartMetric2].map(function (x) {
            var format = null;
            if (x === constants.networkChartMetric.COST) {
                format = 'currency';
            } else if (x === constants.networkChartMetric.CTR) {
                format = 'percent';
            }

            return format;
        });
        
        for (i = 0; i < $scope.dailyStats.length; i++) {
            result.data[0].push([$scope.dailyStats[i].date, $scope.dailyStats[i][$scope.chartMetric1]]);
            
            if ($scope.chartMetric2 && $scope.chartMetric2 !== $scope.chartMetric1) {
                if (!result.data[1]) {
                    result.data[1] = [];
                }
                result.data[1].push([$scope.dailyStats[i].date, $scope.dailyStats[i][$scope.chartMetric2]]);
            }
        }
        $scope.chartData = result;
    };

    $scope.loadRequestInProgress = false;

    $scope.getTableData = function () {
        $scope.loadRequestInProgress = true;

        api.adGroupNetworksTable.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;

                $scope.selectNetworks();
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
        api.adGroupNetworksDailyStats.list($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, null, $scope.selectedNetworkIds).then(
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

    $scope.selectedNetworksChanged = function (networkId) {
        console.log("net");
        var i = 0;
        if (networkId) {
            i = $scope.selectedNetworkIds.indexOf(networkId);
            if (i > -1) {
                $scope.selectedNetworkIds.splice(i, 1);
            } else {
                $scope.selectedNetworkIds.push(networkId);
            }

            if ($scope.selectedNetworkIds.length) {
                $scope.selectedNetworkTotals = false;
            } else {
                $scope.selectedNetworkTotals = true;
            }

            $location.search('network_ids', $scope.selectedNetworkIds.join(','));
        } else {
            $scope.selectedNetworkIds = [];
            $scope.rows.map(function (x) {x.checked = false;});
            if (!$scope.selectedNetworkTotals && !$scope.selectedNetworkIds.length) {
                $scope.selectedNetworkTotals = true;
            }

            $location.search('network_ids', null);
        }

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

    // From parent scope (mainCtrl).
    $scope.$watch('dateRange', function (newValue, oldValue) {
        $scope.getDailyStats();
        $scope.getTableData();
    });

    $scope.selectNetworks = function () {
        $scope.rows.forEach(function (x) {
            if ($scope.selectedNetworkIds.indexOf(x.id) > -1) {
                x.checked = true;
            }
        });
    };

    $scope.$on("$stateChangeSuccess", function() {
        var chartMetric1 = $location.search().chart_metric1;
        var chartMetric2 = $location.search().chart_metric2;
        var chartHidden = $location.search().chart_hidden;
        var networkIds = $location.search().network_ids;
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

        if (networkIds) {
            $scope.selectedNetworkIds = networkIds.split(',');

            if ($scope.selectedNetworkIds) {
                $scope.selectedNetworkTotals = false;
            }

            if ($scope.rows) {
                $scope.selectNetworks();
            }
        }

        if (changed) {
            $scope.setChartData();
        }
    });

    // export
    $scope.downloadReport = function() {
        $window.open('api/ad_groups/' + $state.params.id + '/networks/export/?type=' + $scope.exportType + '&start_date=' + $scope.dateRange.startDate.format() + '&end_date=' + $scope.dateRange.endDate.format(), '_blank');
        $scope.exportType = '';
    };
}]);
