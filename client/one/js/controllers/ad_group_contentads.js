/* globals options, angular, constants, moment */
angular.module('one.legacy').controller('AdGroupAdsCtrl', function ($scope, $window, $state, $location, $q, api, zemAdGroupService, zemContentAdService, zemGridConstants, zemUserSettings, $timeout, zemPostclickMetricsService, zemDataFilterService, zemPermissions, zemChartStorageService, zemNavigationNewService) { // eslint-disable-line max-len
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = options.adGroupChartMetrics;
    $scope.chartIsLoading = false;
    $scope.localStoragePrefix = 'adGroupContentAds';
    $scope.infoboxLinkTo = 'main.adGroups.settings';

    $scope.config = {
        level: constants.level.AD_GROUPS,
        breakdown: constants.breakdown.CONTENT_AD,
        entityId: $state.params.id,
    };

    $scope.grid = {
        options: undefined,
        api: undefined,
    };

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
    var filteredStatusesUpdateHandler = zemDataFilterService.onFilteredStatusesUpdate(getDailyStats);

    $scope.$on('$destroy', function () {
        filteredSourcesUpdateHandler();
        filteredStatusesUpdateHandler();
    });

    $scope.refreshGridAndTable = function () {
        if ($scope.grid && $scope.grid.api) {
            $scope.grid.api.reload();
        }
    };

    var init = function () {
        var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

        setChartOptions();
        initChartMetricsFromLocalStorage();

        getDailyStats();
        getInfoboxData();
        var entityUpdateHandler = zemAdGroupService.onEntityUpdated(function () {
            getInfoboxData();
        });
        $scope.$on('$destroy', entityUpdateHandler);

        var activeEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(initChartMetricsFromLocalStorage);
        $scope.$on('$destroy', activeEntityUpdateHandler);

        var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(function () {
            getDailyStats();
        });
        $scope.$on('$destroy', dateRangeUpdateHandler);

        $scope.setActiveTab();
    };

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

    var unbindApiWatch = $scope.$watch('grid.api', function () {
        if ($scope.grid.api) {
            $scope.grid.api.onSelectionUpdated($scope, getDailyStats);
            unbindApiWatch();
        }
    });

    var dailyStatsPromise = undefined;
    var getDailyStats = function () {
        if ($scope.hasPermission('zemauth.can_see_new_chart')) return;

        if (dailyStatsPromise) {
            dailyStatsPromise.abort();
        }

        $scope.chartIsLoading = true;
        var dateRange = zemDataFilterService.getDateRange();

        var convertedSelection = {};
        if ($scope.grid.api) {
            var selection = $scope.grid.api.getSelection();
            convertedSelection.selectedIds = selection.selected.filter(function (row) {
                return row.level == 1;
            }).map(function (row) {
                return row.id;
            });
            convertedSelection.unselectedIds = selection.unselected.filter(function (row) {
                return row.level == 1;
            }).map(function (row) {
                return row.id;
            });
            convertedSelection.selectAll = selection.type === zemGridConstants.gridSelectionFilterType.ALL;
            convertedSelection.batchId = selection.type === zemGridConstants.gridSelectionFilterType.CUSTOM ?
                selection.filter.batch.id : null;
        }

        dailyStatsPromise = api.dailyStats.list($scope.level, $state.params.id, $scope.config.breakdown, dateRange.startDate,
            dateRange.endDate, convertedSelection, true, getDailyStatsMetrics());
        dailyStatsPromise.then(
            function (data) {
                setChartOptions(data.goals);
                refreshChartOptions(data.conversionGoals, data.pixels);
                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.chartIsLoading = false;
        });
    };

    var getInfoboxData = function () {
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

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

        if ($scope.hasPermission('zemauth.content_ads_postclick_acquisition')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatAcquisitionChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.content_ads_postclick_acquisition')
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

    var refreshChartOptions = function (conversionGoals, pixels) {
        zemPostclickMetricsService.insertConversionsGoalChartOptions($scope.chartMetricOptions, conversionGoals);
        zemPostclickMetricsService.insertPixelChartOptions($scope.chartMetricOptions, pixels);

        var validChartMetrics = zemPostclickMetricsService.getValidChartMetrics($scope.chartMetric1, $scope.chartMetric2, $scope.chartMetricOptions);
        if ($scope.chartMetric1 !== validChartMetrics.metric1) $scope.chartMetric1 = validChartMetrics.metric1;
        if ($scope.chartMetric2 !== validChartMetrics.metric2) $scope.chartMetric2 = validChartMetrics.metric2;
    };

    function initChartMetricsFromLocalStorage () {
        var chartMetrics = zemChartStorageService.loadMetrics();
        if (chartMetrics) {
            $scope.chartMetric1 = chartMetrics.metric1;
            $scope.chartMetric2 = chartMetrics.metric2;
        }
    }

    init();
});
