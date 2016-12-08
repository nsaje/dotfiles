/*globals angular,constants,options,moment*/
angular.module('one.legacy').controller('AccountCampaignsCtrl', function ($window, $location, $scope, $state, $timeout, $q, api, zemAccountService, zemCampaignService, zemPostclickMetricsService, zemFilterService, zemUserSettings, zemNavigationService, zemDataFilterService, zemGridConstants, zemPermissions) { // eslint-disable-line max-len
    $scope.addCampaignRequestInProgress = false;
    $scope.chartHidden = false;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = options.accountChartMetrics;
    $scope.chartIsLoading = false;

    $scope.localStoragePrefix = 'accountCampaigns';
    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.infoboxLinkTo = 'main.accounts.settings';

    $scope.selection = {
        entityIds: [],
        totals: true,
    };

    $scope.grid = {
        api: undefined,
        level: constants.level.ACCOUNTS,
        breakdown: constants.breakdown.CAMPAIGN,
        entityId: $state.params.id,
    };

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    $scope.updateSelectedCampaigns = function (campaignId) {
        campaignId = campaignId.toString();

        var i = $scope.selection.entityIds.indexOf(campaignId);
        if (i > -1) {
            $scope.selection.entityIds.splice(i, 1);
        } else {
            $scope.selection.entityIds.push(campaignId);
        }
    };

    $scope.selectedCampaignsChanged = function (row, checked) {
        if (row.campaign) {
            $scope.updateSelectedCampaigns(row.campaign);
        } else {
            $scope.selection.totals = !$scope.selection.totals;
        }

        $scope.updateSelectedRowsData();
    };

    $scope.updateSelectedRowsData = function () {
        if (!$scope.selection.totals && !$scope.selection.entityIds.length) {
            $scope.selection.totals = true;
        }

        $location.search('campaign_ids', $scope.selection.entityIds.join(','));
        $location.search('campaign_totals', $scope.selection.totals ? 1 : null);

        getDailyStats();
    };

    $scope.addCampaign = function () {
        var accountId = $state.params.id;
        $scope.addCampaignRequestInProgress = true;

        zemCampaignService.create(accountId).then(
            function (campaignData) {
                zemNavigationService.addCampaignToCache(accountId, {
                    id: campaignData.id,
                    name: campaignData.name,
                    adGroups: [],
                });
                $state.go('main.campaigns.ad_groups', {id: campaignData.id, settings: 'create'});
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.addCampaignRequestInProgress = false;
        });
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!$scope.isMetricInChartData(newValue, $scope.chartData)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
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

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.accountChartMetrics;

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

        dailyStatsPromise = api.dailyStats.list($scope.level, $state.params.id, $scope.grid.breakdown, dateRange.startDate, dateRange.endDate, convertedSelection, $scope.selection.totals, getDailyStatsMetrics());
        dailyStatsPromise.then(
            function (data) {
                refreshChartOptions(data.pixels);
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

    var refreshChartOptions = function (pixels) {
        zemPostclickMetricsService.insertPixelChartOptions($scope.chartMetricOptions, pixels);

        var validChartMetrics = zemPostclickMetricsService.getValidChartMetrics($scope.chartMetric1, $scope.chartMetric2, $scope.chartMetricOptions);
        if ($scope.chartMetric1 !== validChartMetrics.metric1) {
            $scope.chartMetric1 = validChartMetrics.metric1;
        }

        if ($scope.chartMetric2 !== validChartMetrics.metric2) {
            $scope.chartMetric2 = validChartMetrics.metric2;
        }
    };

    $scope.getInfoboxData = function () {
        api.accountOverview.get($state.params.id).then(
            function (data) {
                $scope.infoboxHeader = data.header;
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
            }
        );
    };

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;
        $scope.chartBtnTitle = $scope.chartHidden ? 'Show chart' : 'Hide chart';

        $timeout(function () {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    $scope.init = function () {
        var campaignIds = $location.search().campaign_ids;
        var campaignTotals = $location.search().campaign_totals;

        userSettings.registerWithoutWatch('chartMetric1');
        userSettings.registerWithoutWatch('chartMetric2');
        userSettings.registerGlobal('chartHidden');
        setChartOptions();

        if (campaignIds) {
            campaignIds.split(',').forEach(function (id) {
                $scope.updateSelectedCampaigns(id);
            });
            $location.search('campaign_ids', campaignIds);
        }

        $scope.selection.totals = !$scope.selection.entityIds.length || !!campaignTotals;
        $location.search('campaign_totals', campaignTotals);

        getDailyStats();

        $scope.getInfoboxData();
        var entityUpdateHandler = zemAccountService.onEntityUpdated(function () {
            $scope.getInfoboxData();
        });
        $scope.$on('$destroy', entityUpdateHandler);

        $scope.setActiveTab();

        var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(function () {
            getDailyStats();
        });
        $scope.$on('$destroy', dateRangeUpdateHandler);
    };

    $scope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
        $location.search('campaign_ids', null);
        $location.search('campaign_totals', null);
    });

    if (zemPermissions.hasPermission('zemauth.can_see_new_filter_selector')) {
        var filteredSourcesUpdateHandler = zemDataFilterService.onFilteredSourcesUpdate(getDailyStats);
        $scope.$on('$destroy', filteredSourcesUpdateHandler);
    } else {
        $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            getDailyStats();
        }, true);
    }

    $scope.init();
});
