/*globals oneApp, options*/
oneApp.controller('CampaignAdGroupsCtrl', ['$scope', '$state', 'api', 'zemChartService', '$location', 'localStorageService', function ($scope, $state, api, zemChartService, $location, localStorageService) {
    $scope.requestInProgress = false;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.chartMetric1 = constants.sourceChartMetric.CLICKS;
    $scope.chartMetric2 = constants.sourceChartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetrics = options.sourceChartMetrics;
    $scope.chartGoalMetrics = null;
    $scope.selectedAdGroupIds = [];
    $scope.selectedTotals = true;

    $scope.addAdGroup = function () {
        var campaignId = $state.params.id;
        $scope.requestInProgress = true;

        api.campaignAdGroups.create(campaignId).then(
            function (data) {
                $scope.accounts.forEach(function (account) {
                    account.campaigns.forEach(function (campaign) {
                        if (campaign.id.toString() === campaignId.toString()) {
                            campaign.adGroups.push({
                                id: data.id,
                                name: data.name
                            });

                            $state.go('main.adGroups.settings', {id: data.id});
                        }
                    });
                });
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.getDailyStats();
            $location.search('chart_metric1', $scope.chartMetric1);
            localStorageService.set('campaignAdGroups.chartMetric1', $scope.chartMetric1);
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.getDailyStats();
            $location.search('chart_metric2', $scope.chartMetric2);
            localStorageService.set('campaignAdGroups.chartMetric2', $scope.chartMetric2);
        }
    });

    $scope.getDailyStats = function () {
        api.campaignDailyStats.list($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedAdGroupIds, $scope.selectedTotals, $scope.chartMetric1, $scope.chartMetric2).then(
            function (data) {
                $scope.chartMetricOptions = options.sourceChartMetrics.concat(Object.keys(data.goals).map(function (goalId) {
                    return {
                        name: data.goals[goalId].name,
                        value: goalId
                    };
                }));

                $scope.chartGoalMetrics = data.goals;
                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.init = function() {
        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get('campaignAdGroups.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get('campaignAdGroups.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;
        var order = $location.search().order || localStorageService.get('campaignAdGroups.order') || $scope.order;

        var data = $scope.adGroupData[$state.params.id];
        var adGroupIds = $location.search().ad_group_ids || (data && data.adGroupIds && data.adGroupIds.join(','));
        var adGroupTotals = $location.search().ad_group_totals || (data && data.adGroupTotals ? 1 : null);

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

        if (adGroupIds) {
            $scope.selectedAdGroupIds = adGroupIds.split(',');
            $location.search('ad_group_ids', adGroupIds);

            if ($scope.rows) {
                $scope.selectAdGroups();
            }
        }

        if (order !== undefined && $scope.order !== order) {
            $scope.order = order;
            $location.search('order', order);
        }

        $scope.selectedTotals = !$scope.selectedAdGroupIds.length || !!adGroupTotals;
        $location.search('ad_group_totals', adGroupTotals);

        $scope.getDailyStats();
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('ad_group_ids', null);
        $location.search('ad_group_totals', null);
        $location.search('chart_metric1', null);
        $location.search('chart_metric2', null);
    });

    $scope.init();
}]);
