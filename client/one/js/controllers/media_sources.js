/* globals moment,constants,options,angular */
angular.module('one.legacy').controller('MediaSourcesCtrl', function ($scope, $state, zemUserSettings, $location, api, zemPostclickMetricsService, $timeout, zemDataFilterService, zemGridConstants, zemPermissions, zemChartStorageService, zemNavigationNewService) { // eslint-disable-line max-len
    $scope.localStoragePrefix = null;
    $scope.chartMetrics = [];
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = [];
    $scope.chartIsLoading = false;

    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.infoboxLinkTo = null;
    $scope.sideBarVisible = false;

    $scope.selection = {
        entityIds: [],
        totals: true,
    };

    $scope.grid = {
        api: undefined,
        level: $scope.level,
        breakdown: constants.breakdown.MEDIA_SOURCE,
        entityId: $state.params.id,
    };

    var userSettings = null,
        hasCampaignGoals = $scope.level === constants.level.CAMPAIGNS;

    $scope.updateSelectedSources = function (sourceId) {
        var i = $scope.selection.entityIds.indexOf(sourceId);

        if (i > -1) {
            $scope.selection.entityIds.splice(i, 1);
        } else {
            $scope.selection.entityIds.push(sourceId);
        }
    };

    $scope.updateSelectedRowsLocation = function () {
        if (!$scope.selection.totals && !$scope.selection.entityIds.length) {
            $scope.selection.totals = true;
        }
        if ($scope.selection.entityIds.length > 0) {
            $location.search('source_ids', $scope.selection.entityIds.join(','));
            $location.search('source_totals', $scope.selection.totals ? 1 : null);
        } else {
            $location.search('source_ids', null);
            $location.search('source_totals', null);
        }
    };

    $scope.updateSelectedRowsData = function () {
        $scope.updateSelectedRowsLocation();
        getDailyStats();
    };

    $scope.selectedSourceRemoved = function (sourceId) {
        if (sourceId !== 'totals') {
            $scope.updateSelectedSources(String(sourceId));
        } else {
            $scope.selection.totals = false;
        }

        $scope.updateSelectedRowsData();
    };

    $scope.removeFilteredSelectedSources = function () {
        var filteredSources = zemDataFilterService.getFilteredSources();
        if (filteredSources.length > 0) {
            $scope.selection.entityIds = $scope.selection.entityIds.filter(function (sourceId) {
                return filteredSources.indexOf(sourceId) !== -1;
            });
        }
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!$scope.isMetricInChartData(newValue, $scope.chartData)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
            zemChartStorageService.saveMetrics(
                {metric1: $scope.chartMetric1, metric2: $scope.chartMetric2},
                $scope.level
            );
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
            zemChartStorageService.saveMetrics(
                {metric1: $scope.chartMetric1, metric2: $scope.chartMetric2},
                $scope.level
            );
        }
    });

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

    var dailyStatsPromise = undefined;
    var getDailyStats = function () {
        if (dailyStatsPromise) {
            dailyStatsPromise.abort();
        }

        $scope.chartIsLoading = true;

        var convertedSelection = {selectedIds: $scope.selection.entityIds};
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
        }

        var dateRange = zemDataFilterService.getDateRange();
        dailyStatsPromise = api.dailyStats.list($scope.level, $state.params.id, $scope.grid.breakdown, dateRange.startDate,
            dateRange.endDate, convertedSelection, $scope.selection.totals, getDailyStatsMetrics());

        dailyStatsPromise.then(
            function (data) {
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

    var updateInfoboxData = function (data) {
        $scope.infoboxHeader = data.header;
        $scope.infoboxBasicSettings = data.basicSettings;
        $scope.infoboxPerformanceSettings = data.performanceSettings;
        $scope.reflowGraph(1);
    };

    $scope.getInfoboxData = function () {
        var dateRange = zemDataFilterService.getDateRange();
        if ($scope.level === constants.level.ALL_ACCOUNTS) {
            api.allAccountsOverview.get(dateRange.startDate, dateRange.endDate).then(
                function (data) {
                    updateInfoboxData(data);
                }
            );
        } else if ($scope.level === constants.level.ACCOUNTS) {
            api.accountOverview.get($state.params.id).then(
                function (data) {
                    updateInfoboxData(data);
                }
            );
        } else if ($scope.level === constants.level.CAMPAIGNS) {
            api.campaignOverview.get(
                $state.params.id,
                dateRange.startDate,
                dateRange.endDate
            ).then(
                function (data) {
                    updateInfoboxData(data);
                }
            );
        }
    };

    var setChartOptions = function () {
        $scope.chartMetricOptions = $scope.chartMetrics;

        if ($scope.hasPermission('zemauth.aggregate_postclick_acquisition')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatAcquisitionChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.aggregate_postclick_acquisition')
            );
        }

        if ($scope.hasPermission('zemauth.aggregate_postclick_engagement')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatEngagementChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.aggregate_postclick_engagement')
            );
        }

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

    function initChartMetricsFromLocalStorage () {
        var chartMetrics = zemChartStorageService.loadMetrics($scope.level);
        if (chartMetrics) {
            $scope.chartMetric1 = chartMetrics.metric1;
            $scope.chartMetric2 = chartMetrics.metric2;
        }
    }

    var init = function () {
        if ($scope.level === constants.level.ALL_ACCOUNTS) {
            $scope.localStoragePrefix = 'allAccountSources';
            $scope.chartMetrics = options.allAccountsChartMetrics;
            $scope.chartMetric1 = constants.chartMetric.COST;
            $scope.chartMetric2 = constants.chartMetric.CLICKS;
        } else if ($scope.level === constants.level.ACCOUNTS) {
            $scope.localStoragePrefix = 'accountSources';
            $scope.chartMetrics = options.accountChartMetrics;
            $scope.infoboxLinkTo = 'main.accounts.settings';
        } else if ($scope.level === constants.level.CAMPAIGNS) {
            $scope.localStoragePrefix = 'campaignSources';
            $scope.chartMetrics = options.campaignChartMetrics;
            $scope.infoboxLinkTo = 'main.campaigns.settings';
        }

        userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

        var sourceIds = $location.search().source_ids;
        var sourceTotals = $location.search().source_totals;

        setChartOptions();
        initChartMetricsFromLocalStorage();

        if (sourceIds) {
            $scope.selection.entityIds = sourceIds.split(',');
            $scope.removeFilteredSelectedSources();
            $location.search('source_ids', sourceIds);
        }

        $scope.selection.totals = !$scope.selection.entityIds.length || !!sourceTotals;
        $location.search('source_totals', sourceTotals);

        getDailyStats();
        $scope.getInfoboxData();

        if ($scope.hasPermission('zemauth.can_view_sidetabs') && $scope.level === constants.level.CAMPAIGNS) {
            $scope.sideBarVisible = true;
            $scope.getContentInsights();
        } else {
            $scope.sideBarVisible = false;
        }

        $scope.setActiveTab();

        var activeEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(initChartMetricsFromLocalStorage);
        $scope.$on('$destroy', activeEntityUpdateHandler);
    };

    var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(function () {
        if ($scope.level === constants.level.ALL_ACCOUNTS) {
            $scope.getInfoboxData();
        }
        getDailyStats();

        if ($scope.hasPermission('zemauth.can_view_sidetabs') && $scope.level === constants.level.CAMPAIGNS) {
            $scope.sideBarVisible = true;
            $scope.getContentInsights();
        }
    });
    $scope.$on('$destroy', dateRangeUpdateHandler);

    var filteredSourcesUpdateHandler = zemDataFilterService.onFilteredSourcesUpdate(getDailyStats);
    $scope.$on('$destroy', filteredSourcesUpdateHandler);

    $scope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
        $location.search('source_ids', null);
        $location.search('source_totals', null);
    });

    init();
});
