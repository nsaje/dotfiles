/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupNetworksCtrl', ['$scope', '$state', '$location', 'api', function ($scope, $state, $location, api) {
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.networkChartMetric.CLICKS;
    $scope.chartMetric2 = constants.networkChartMetric.IMPRESSIONS;
    $scope.dailyStats = [];
    $scope.chartData = [];
    $scope.isChartShown = true;
    $scope.chartBtnTitle = 'Hide chart';

    $scope.setChartData = function () {
        var result = [[]];
        var i;
        for (i = 0; i < $scope.dailyStats.length; i++) {
            result[0].push([$scope.dailyStats[i].date, $scope.dailyStats[i][$scope.chartMetric1]]);
            
            if ($scope.chartMetric2 && $scope.chartMetric2 !== $scope.chartMetric1) {
                if (!result[1]) {
                    result[1] = [];
                }
                result[1].push([$scope.dailyStats[i].date, $scope.dailyStats[i][$scope.chartMetric2]]);
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
