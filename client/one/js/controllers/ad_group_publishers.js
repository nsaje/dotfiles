/*globals angular,moment,constants,options*/

angular.module('one.legacy').controller('AdGroupPublishersCtrl', function ($scope, $state, $location, $timeout, $window, api, zemPostclickMetricsService, zemUserSettings, zemDataFilterService, zemPermissions, zemChartStorageService, zemNavigationNewService) {
    $scope.constants = constants;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = [];
    $scope.chartGoalMetrics = null;
    $scope.chartIsLoading = false;
    $scope.localStoragePrefix = 'adGroupPublishers';
    $scope.infoboxLinkTo = 'main.adGroups.settings';
    $scope.tab = {
        name: 'Publishers'
    };

    $scope.config = {
        level: constants.level.AD_GROUPS,
        breakdown: constants.breakdown.PUBLISHER,
        entityId: $state.params.id,
    };

    $scope.grid = {
        api: undefined,
    };

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    // HACK: Just to make binding with zem-chart-legacy work (it will be replaced in near future with zem-chart)
    // (adding ng-if for permission makes binding stop working)
    $scope._chartMetrics = {
        metric1: constants.chartMetric.CLICKS,
        metric2: constants.chartMetric.IMPRESSIONS
    };
    $scope.$watch('_chartMetrics', function (newValue, oldValue) {
        $scope.chartMetric1 = $scope._chartMetrics.metric1;
        $scope.chartMetric2 = $scope._chartMetrics.metric2;
    }, true);

    var getDailyStatsMetrics = function () {
        // always query for default metrics
        var metrics = [$scope.chartMetric1, $scope.chartMetric2];
        if (metrics.indexOf(constants.chartMetric.CLICKS) < 0) {
            metrics.push(constants.chartMetric.CLICKS);
        }
        if (metrics.indexOf(constants.chartMetric.IMPRESSIONS) < 0) {
            metrics.push(constants.chartMetric.IMPRESSIONS);
        }
        return metrics;
    };

    var refreshChartOptions = function (conversionGoals, pixels) {
        zemPostclickMetricsService.insertConversionsGoalChartOptions($scope.chartMetricOptions, conversionGoals);
        zemPostclickMetricsService.insertPixelChartOptions($scope.chartMetricOptions, pixels);

        var validChartMetrics = zemPostclickMetricsService.getValidChartMetrics($scope.chartMetric1, $scope.chartMetric2, $scope.chartMetricOptions);
        if ($scope.chartMetric1 !== validChartMetrics.metric1) $scope.chartMetric1 = validChartMetrics.metric1;
        if ($scope.chartMetric2 !== validChartMetrics.metric2) $scope.chartMetric2 = validChartMetrics.metric2;
    };

    var setChartOptions = function (goals) {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

        if ($scope.hasPermission('zemauth.view_pubs_postclick_acquisition')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatAcquisitionChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.view_pubs_postclick_acquisition')
            );
        }

        $scope.chartMetricOptions = zemPostclickMetricsService.concatEngagementChartOptions(
            $scope.chartMetricOptions,
            false
        );

        if ($scope.hasPermission('zemauth.can_view_platform_cost_breakdown')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                options.platformCostChartMetrics,
                $scope.isPermissionInternal('zemauth.can_view_platform_cost_breakdown')
            );
        }

        $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
            $scope.chartMetricOptions,
            options.billingCostChartMetrics,
            false
        );

        if ($scope.hasPermission('zemauth.can_view_actual_costs')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                options.actualCostChartMetrics,
                $scope.isPermissionInternal('zemauth.can_view_actual_costs')
            );
        }

        $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
            $scope.chartMetricOptions,
            options.conversionChartMetrics
        );

        $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
            $scope.chartMetricOptions,
            options.goalChartMetrics
        );
    };

    var dailyStatsPromise = undefined;
    var getDailyStats = function () {
        if ($scope.hasPermission('zemauth.can_see_new_chart')) return;

        if (dailyStatsPromise) {
            dailyStatsPromise.abort();
        }

        $scope.chartIsLoading = true;

        var dateRange = zemDataFilterService.getDateRange();
        dailyStatsPromise = api.dailyStats.listPublishersStats($state.params.id, dateRange.startDate, dateRange.endDate, [], true, getDailyStatsMetrics());
        dailyStatsPromise.then(
            function (data) {
                refreshChartOptions(data.conversionGoals, data.pixels);

                $scope.chartData = data.chartData;
                $scope.chartGoalMetrics = data.goals;
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.chartIsLoading = false;
        });
    };

    $scope.getInfoboxData = function () {
        var dateRange = zemDataFilterService.getDateRange();
        api.adGroupOverview.get(
            $state.params.id,
            dateRange.startDate,
            dateRange.endDate).then(
            function (data) {
                $scope.setInfoboxHeader(data.header);
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
            }
        );
    };

    function initChartMetricsFromLocalStorage () {
        var chartMetrics = zemChartStorageService.loadMetrics();
        if (chartMetrics) {
            $scope.chartMetric1 = chartMetrics.metric1;
            $scope.chartMetric2 = chartMetrics.metric2;
        }
    }

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!$scope.isMetricInChartData(newValue, $scope.chartData)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
            zemChartStorageService.saveMetrics({metric1: $scope.chartMetric1, metric2: $scope.chartMetric2});
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!$scope.isMetricInChartData(newValue, $scope.chartData)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
            zemChartStorageService.saveMetrics({metric1: $scope.chartMetric1, metric2: $scope.chartMetric2});
        }
    });

    var filteredSourcesUpdateHandler = zemDataFilterService.onFilteredSourcesUpdate(getDailyStats);
    var filteredPublisherStatusUpdateHandler = zemDataFilterService.onFilteredPublisherStatusUpdate(getDailyStats);

    $scope.$on('$destroy', function () {
        filteredSourcesUpdateHandler();
        filteredPublisherStatusUpdateHandler();
    });

    $scope.init = function () {
        var data = $scope.adGroupData[$state.params.id];

        setChartOptions();
        initChartMetricsFromLocalStorage();

        getDailyStats();
        $scope.getInfoboxData();

        var activeEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(initChartMetricsFromLocalStorage);
        var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(getDailyStats);
        $scope.$on('$destroy', function () {
            activeEntityUpdateHandler();
            dateRangeUpdateHandler();
        });

        $scope.setActiveTab();
    };

    $scope.init();
});
