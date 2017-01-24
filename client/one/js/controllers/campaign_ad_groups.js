/* globals moment,constants,options,angular */
angular.module('one.legacy').controller('CampaignAdGroupsCtrl', function ($location, $scope, $state, $timeout, api, zemCampaignService, zemAdGroupService, zemPostclickMetricsService, zemUserSettings, zemNavigationService, zemDataSourceService, zemGridEndpointService, zemDataFilterService, zemGridConstants, zemPermissions, zemChartStorageService, zemNavigationNewService) { // eslint-disable-line max-len
    $scope.addGroupRequestInProgress = false;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = options.campaignChartMetrics;
    $scope.chartIsLoading = false;
    $scope.isIncompletePostclickMetrics = false;
    $scope.localStoragePrefix = 'campaignAdGroups';
    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.infoboxLinkTo = 'main.campaigns.settings';

    $scope.selection = {
        entityIds: [],
        totals: true,
    };

    $scope.config = {
        level: constants.level.CAMPAIGNS,
        breakdown: constants.breakdown.AD_GROUP,
        entityId: $state.params.id,
    };

    $scope.grid = {
        options: undefined,
        api: undefined,
    };

    var userSettings = zemUserSettings.getInstance($scope, 'campaignAdGroups');

    $scope.updateSelectedAdGroups = function (adGroupId) {
        adGroupId = adGroupId.toString();

        var i = $scope.selection.entityIds.indexOf(adGroupId);
        if (i > -1) {
            $scope.selection.entityIds.splice(i, 1);
        } else {
            $scope.selection.entityIds.push(adGroupId);
        }
    };

    $scope.selectedAdGroupsChanged = function (row, checked) {
        if (row.ad_group) {
            $scope.updateSelectedAdGroups(row.ad_group);
        } else {
            $scope.selection.totals = !$scope.selection.totals;
        }

        $scope.updateSelectedRowsData();
    };

    $scope.updateSelectedRowsData = function () {
        if (!$scope.selection.totals && !$scope.selection.entityIds.length) {
            $scope.selection.totals = true;
        }

        $location.search('ad_group_ids', $scope.selection.entityIds.join(','));
        $location.search('ad_group_totals', $scope.selection.totals ? 1 : null);

        getDailyStats();
    };

    $scope.addAdGroup = function () {
        var campaignId = $state.params.id;
        $scope.addGroupRequestInProgress = true;

        zemAdGroupService.create(campaignId).then(
            function (data) {
                zemNavigationService.addAdGroupToCache(campaignId, {
                    id: data.id,
                    name: data.name,
                    status: constants.settingsState.INACTIVE,
                    state: constants.adGroupRunningStatus.INACTIVE,
                });
                $state.go('main.adGroups.ads', {id: data.id, settings: 'create'});
            },
            function () {
                // error
                return;
            }
        ).finally(function () {
            $scope.addGroupRequestInProgress = false;
        });
    };

    $scope.getInfoboxData = function () {
        var dateRange = zemDataFilterService.getDateRange();
        api.campaignOverview.get(
            $state.params.id,
            dateRange.startDate,
            dateRange.endDate
        ).then(
            function (data) {
                $scope.infoboxHeader = data.header;
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
            }
        );
    };

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

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.campaignChartMetrics;

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

    var dailyStatsPromise = undefined;
    var getDailyStats = function () {
        if ($scope.hasPermission('zemauth.can_see_new_chart')) return;

        if (dailyStatsPromise) {
            dailyStatsPromise.abort();
        }

        $scope.chartIsLoading = true;
        var dateRange = zemDataFilterService.getDateRange();

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

        dailyStatsPromise = api.dailyStats.list($scope.level, $state.params.id, $scope.config.breakdown, dateRange.startDate, dateRange.endDate, convertedSelection, $scope.selection.totals, getDailyStatsMetrics());
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

    function initChartMetricsFromLocalStorage () {
        var chartMetrics = zemChartStorageService.loadMetrics();
        if (chartMetrics) {
            $scope.chartMetric1 = chartMetrics.metric1;
            $scope.chartMetric2 = chartMetrics.metric2;
        }
    }

    $scope.init = function () {
        var adGroupIds = $location.search().ad_group_ids;
        var adGroupTotals = $location.search().ad_group_totals;

        setChartOptions();
        initChartMetricsFromLocalStorage();

        userSettings.register('order');

        if (adGroupIds) {
            adGroupIds.split(',').forEach(function (id) {
                $scope.updateSelectedAdGroups(id);
            });
            $location.search('ad_group_ids', adGroupIds);
        }

        $scope.selection.totals = !$scope.selection.entityIds.length || !!adGroupTotals;
        $location.search('ad_group_totals', adGroupTotals);

        getDailyStats();
        $scope.getContentInsights();

        $scope.getInfoboxData();

        var activeEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(initChartMetricsFromLocalStorage);
        var entityUpdateHandler = zemCampaignService.onEntityUpdated(function () {
            $scope.getInfoboxData();
        });
        $scope.$on('$destroy', function () {
            activeEntityUpdateHandler();
            entityUpdateHandler();
        });

        $scope.setActiveTab();
    };

    $scope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
        $location.search('ad_group_ids', null);
        $location.search('ad_group_totals', null);
    });

    var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(function () {
        getDailyStats();
        $scope.getContentInsights();
    });
    $scope.$on('$destroy', dateRangeUpdateHandler);

    var filteredSourcesUpdateHandler = zemDataFilterService.onFilteredSourcesUpdate(getDailyStats);
    $scope.$on('$destroy', filteredSourcesUpdateHandler);

    $scope.init();
});
