/*globals oneApp*/
oneApp.controller('CampaignAdGroupsCtrl', ['$scope', '$state', 'api', 'zemChartService', function ($scope, $state, api, zemChartService) {
    $scope.requestInProgress = false;
    $scope.isChartShown = zemChartService.load('zemChart');

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




    $scope.chartMetric1 = constants.sourceChartMetric.CLICKS;
    $scope.chartMetric2 = constants.sourceChartMetric.IMPRESSIONS;
    $scope.dailyStats = [];
    $scope.chartData = undefined;
    $scope.chartMetrics = options.sourceChartMetrics;

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

        var temp = {};
        var lastDate = null;
        var oneDayMs = 24*60*60*1000;
        $scope.dailyStats.forEach(function (stat) {
            if (!temp.hasOwnProperty(stat.sourceId)) {
                temp[stat.sourceId] = {
                    name: stat.sourceName,
                    id: stat.sourceId,
                    data: [[]]
                };
            }

            // insert nulls for missing values
            if (lastDate) {
                for (var date = lastDate; date < stat.date - oneDayMs; date += oneDayMs) {
                    temp[stat.sourceId].data[0].push([date, null]);

                    if (temp[stat.sourceId].data[1]) {
                        temp[stat.sourceId].data[1].push([date, null]);
                    }
                }
            }
            lastDate = stat.date;

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
            result.names.push(temp[sourceId].name);
            result.ids.push(temp[sourceId].id);
        });

        $scope.chartData = result;

        // TODO REMOVE
        $scope.chartData = {
            metrics: [
                {
                    name: 'CTR',
                    id: 'ctr',
                    format: 'percent'
                },
                {
                    name: 'Cost',
                    id: 'cost',
                    format: 'currency'
                },
            
            ],
            seriesGroups: [
                {
                    id: '12',
                    name: 'Outbrain',
                    seriesData: [
                        [
                            [1404691200000, 25],
                            [1404777600000, 11],
                            [1404864000000, 39],
                        ],
                        [
                            [1404691200000, 35],
                            [1404777600000, 21],
                            [1404864000000, 49],
                        ],
                    ]
                }, {
                    id: 'totals',
                    name: 'Totals',
                    seriesData: [
                        [
                            [1404691200000, 45],
                            [1404777600000, null],
                            [1404864000000, 89],
                        ],
                    ]
                }
            ]
        };
    };

    $scope.getDailyStats = function () {
        api.adGroupDailyStats.list($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedSourceIds, $scope.selectedSourceTotals).then(
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

    $scope.getDailyStats();
}]);
