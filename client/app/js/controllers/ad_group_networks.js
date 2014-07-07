/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupNetworksCtrl', ['$scope', '$state', '$location', 'api', 'zemCustomTableColsService', function ($scope, $state, $location, api, zemCustomTableColsService) {
    $scope.isSyncRecent = true;
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
        }
    ];

    zemCustomTableColsService.load('adGroupNetworksCols', $scope.columns);
    $scope.$watch('columns', function (newValue, oldValue) {
        zemCustomTableColsService.save('adGroupNetworksCols', newValue);
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
                $scope.lastSyncDate = moment(data.last_sync);
                $scope.isSyncRecent = data.is_sync_recent;
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
        api.adGroupNetworksDailyStats.list($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate).then(
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

    $scope.$on("$stateChangeSuccess", function() {
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
    });
}]);
