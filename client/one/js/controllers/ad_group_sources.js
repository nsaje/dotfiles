/*globals angular,moment,constants,options*/

angular.module('one.legacy').controller('AdGroupSourcesCtrl', function ($scope, $state, $location, $timeout, $window, api, zemPostclickMetricsService, zemUserSettings, zemNavigationService, zemDataFilterService, zemGridConstants, zemPermissions, zemChartStorageService, zemNavigationNewService) {
    $scope.constants = constants;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = [];
    $scope.chartIsLoading = false;
    $scope.sources = [];
    $scope.sourcesWaiting = null;
    $scope.infoboxLinkTo = 'main.adGroups.settings';
    $scope.localStoragePrefix = 'adGroupSources';

    $scope.selection = {
        entityIds: [],
        totals: true,
    };

    $scope.grid = {
        api: undefined,
        level: constants.level.AD_GROUPS,
        breakdown: constants.breakdown.MEDIA_SOURCE,
        entityId: $state.params.id,
    };

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    $scope.updateSelectedSources = function (sourceId) {
        var i = $scope.selection.entityIds.indexOf(sourceId);

        if (i > -1) {
            $scope.selection.entityIds.splice(i, 1);
        } else {
            $scope.selection.entityIds.push(sourceId);
        }
    };

    $scope.selectedSourcesChanged = function (row, checked) {
        if (row.id) {
            $scope.updateSelectedSources(row.id);
        } else {
            $scope.selection.totals = !$scope.selection.totals;
        }

        $scope.updateSelectedRowsData();
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

        $scope.setAdGroupData('sourceIds', $scope.selection.entityIds);
        $scope.setAdGroupData('sourceTotals', $scope.selection.totals);
    };

    $scope.updateSelectedRowsData = function () {
        $scope.updateSelectedRowsLocation();
        $scope.getDailyStats();
    };

    $scope.removeFilteredSelectedSources = function () {
        var filteredSources = zemDataFilterService.getFilteredSources();
        if (filteredSources.length > 0) {
            $scope.selection.entityIds = $scope.selection.entityIds.filter(function (sourceId) {
                return filteredSources.indexOf(sourceId) !== -1;
            });
        }
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

    var refreshChartOptions = function (conversionGoals, pixels) {
        zemPostclickMetricsService.insertConversionsGoalChartOptions($scope.chartMetricOptions, conversionGoals);
        zemPostclickMetricsService.insertPixelChartOptions($scope.chartMetricOptions, pixels);

        var validChartMetrics = zemPostclickMetricsService.getValidChartMetrics($scope.chartMetric1, $scope.chartMetric2, $scope.chartMetricOptions);
        if ($scope.chartMetric1 !== validChartMetrics.metric1) $scope.chartMetric1 = validChartMetrics.metric1;
        if ($scope.chartMetric2 !== validChartMetrics.metric2) $scope.chartMetric2 = validChartMetrics.metric2;
    };

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

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
    $scope.getDailyStats = function () {
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

        dailyStatsPromise = api.dailyStats.list($scope.level, $state.params.id, $scope.grid.breakdown, dateRange.startDate, dateRange.endDate, convertedSelection, $scope.selection.totals, getDailyStatsMetrics(), null);
        dailyStatsPromise.then(
            function (data) {
                refreshChartOptions(data.conversionGoals, data.pixels);
                $scope.conversionGoals = data.conversionGoals;
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

    $scope.selectedSourceRemoved = function (sourceId) {
        if (sourceId !== 'totals') {
            $scope.updateSelectedSources(String(sourceId));
        } else {
            $scope.selection.totals = false;
        }

        $scope.selectRows();
        $scope.updateSelectedRowsData();
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!$scope.isMetricInChartData(newValue, $scope.chartData)) {
                $scope.getDailyStats();
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
                $scope.getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
            zemChartStorageService.saveMetrics({metric1: $scope.chartMetric1, metric2: $scope.chartMetric2});
        }
    });

    var filteredSourcesUpdateHandler = zemDataFilterService.onFilteredSourcesUpdate($scope.getDailyStats);
    $scope.$on('$destroy', filteredSourcesUpdateHandler);

    $scope.init = function () {
        var data = $scope.adGroupData[$state.params.id];
        var sourceIds = $location.search().source_ids || (data && data.sourceIds && data.sourceIds.join(','));
        var sourceTotals = $location.search().source_totals || (data && data.sourceTotals ? 1 : null);

        setChartOptions();
        initChartMetricsFromLocalStorage();

        if (sourceIds) {
            $scope.selection.entityIds = sourceIds.split(',');
            $scope.removeFilteredSelectedSources();
            $scope.setAdGroupData('sourceIds', $scope.selection.entityIds);
            $location.search('source_ids', sourceIds);
        }

        $scope.selection.totals = !$scope.selection.entityIds.length || !!sourceTotals;
        $scope.setAdGroupData('sourceTotals', $scope.selection.totals);
        $location.search('source_totals', sourceTotals);

        $scope.getDailyStats();
        getInfoboxData();

        getSources();

        var activeEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(initChartMetricsFromLocalStorage);
        var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(function () {
            $scope.getDailyStats();
        });
        $scope.$on('$destroy', function () {
            activeEntityUpdateHandler();
            dateRangeUpdateHandler();
        });

        $scope.setActiveTab();
    };

    var getSources = function () {
        if (!$scope.hasPermission('zemauth.ad_group_sources_add_source')) {
            return;
        }

        api.adGroupSources.get($state.params.id).then(
            function (data) {
                var sources = [];
                for (var source, i = 0; i < data.sources.length; i++) {
                    source = data.sources[i];

                    var notificationMsg = '';
                    if (!source.canTargetExistingRegions) {
                        notificationMsg = source.name + ' doesn\'t support DMA targeting. Turn off DMA targeting to add ' + source.name + '.';
                    }
                    if (!source.canRetarget) {
                        notificationMsg = (notificationMsg ? notificationMsg + ' ' : '') + source.name + ' doesn\'t support retargeting. Turn off retargeting to add ' + source.name + '.';
                    }
                    sources.push({
                        name: source.name,
                        value: source.id,
                        hasPermission: true,
                        disabled: !source.canTargetExistingRegions || !source.canRetarget,
                        notification: notificationMsg,
                    });
                }

                $scope.sources = sources;
                $scope.sourcesWaiting = data.sourcesWaiting;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.addSource = function (sourceIdToAdd) {
        if (!sourceIdToAdd) {
            return;
        }

        api.adGroupSources.add($state.params.id, sourceIdToAdd).then(
            function (data) {
                getSources();
                if ($scope.grid && $scope.grid.api) {
                    $scope.grid.api.loadData();
                }
            },
            function (data) {
                // error
                return;
            }
        );

        $scope.sourceIdToAdd = '';
    };

    zemNavigationService.onUpdate($scope, function () {
        $scope.updateInfoboxHeader($scope);
    });

    function initChartMetricsFromLocalStorage () {
        var chartMetrics = zemChartStorageService.loadMetrics();
        if (chartMetrics) {
            $scope.chartMetric1 = chartMetrics.metric1;
            $scope.chartMetric2 = chartMetrics.metric2;
        }
    }

    $scope.init();
});
