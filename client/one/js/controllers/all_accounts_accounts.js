/*globals angular,moment,constants,options*/
angular.module('one.legacy').controller('AllAccountsAccountsCtrl', function ($scope, $state, $timeout, api, zemAccountService, zemPostclickMetricsService, zemUserSettings, zemNavigationService, zemDataFilterService, zemGridConstants, zemPermissions, zemChartStorageService, zemNavigationNewService) { // eslint-disable-line max-len
    $scope.requestInProgress = false;
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.chartMetric.COST;
    $scope.chartMetric2 = constants.chartMetric.CLICKS;
    $scope.chartMetricOptions = options.allAccountsChartMetrics;
    $scope.chartData = undefined;
    $scope.chartIsLoading = false;
    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.localStoragePrefix = 'allAccountsAccounts';

    $scope.selection = {
        entityIds: [],
        totals: true,
    };
    $scope.config = {
        entityId: undefined,
        level: constants.level.ALL_ACCOUNTS,
        breakdown: constants.breakdown.ACCOUNT,
    };
    $scope.grid = {
        api: undefined,
    };
    if (!$scope.hasPermission('zemauth.bulk_actions_on_all_levels')) {
        $scope.grid.options = {};
    }

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
    $scope.setModels(null);

    $scope.addAccount = function () {
        $scope.requestInProgress = true;

        zemAccountService.create().then(
            function (data) {
                zemNavigationService.addAccountToCache({
                    'name': data.name,
                    'id': data.id,
                    'campaigns': [],
                });
                $state.go('main.accounts.campaigns', {id: data.id, settings: 'create'});
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    var getDailyStatsMetrics = function () {
        var values = $scope.chartMetricOptions.map(function (option) {
            return option.value;
        });

        // always query for default metrics
        var metrics = [constants.chartMetric.CLICKS, constants.chartMetric.IMPRESSIONS];
        if (values.indexOf($scope.chartMetric1) === -1) {
            $scope.chartMetric1 = constants.chartMetric.CLICKS;
        } else {
            metrics.push($scope.chartMetric1);
        }

        if ($scope.chartMetric2 !== 'none' && values.indexOf($scope.chartMetric2) === -1) {
            $scope.chartMetric2 = constants.chartMetric.COST;
        } else {
            metrics.push($scope.chartMetric2);
        }

        return metrics;
    };

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.allAccountsChartMetrics;

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
            options.goalChartMetrics,
            false
        );
    };

    $scope.updateSelectedRowsData = function () {
        getDailyStats();
    };

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
        }

        dailyStatsPromise = api.dailyStats.list($scope.level, null, $scope.config.breakdown, dateRange.startDate, dateRange.endDate, convertedSelection, true, getDailyStatsMetrics());
        dailyStatsPromise.then(
            function (data) {
                setChartOptions();
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

    $scope.getInfoboxData = function () {
        var dateRange = zemDataFilterService.getDateRange();
        api.allAccountsOverview.get(dateRange.startDate, dateRange.endDate).then(
            function (data) {
                $scope.infoboxHeader = data.header;
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
            }
        );
    };

    var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(function () {
        $scope.getInfoboxData();
        getDailyStats();
    });
    $scope.$on('$destroy', dateRangeUpdateHandler);

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            getDailyStats();
            zemChartStorageService.saveMetrics(
                {metric1: $scope.chartMetric1, metric2: $scope.chartMetric2},
                constants.level.ALL_ACCOUNTS
            );
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            getDailyStats();
            zemChartStorageService.saveMetrics(
                {metric1: $scope.chartMetric1, metric2: $scope.chartMetric2},
                constants.level.ALL_ACCOUNTS
            );
        }
    });

    var filteredSourcesUpdateHandler = zemDataFilterService.onFilteredSourcesUpdate(getDailyStats);
    var filteredAgenciesUpdateHandler = zemDataFilterService.onFilteredAgenciesUpdate(function () {
        getDailyStats();
        $scope.getInfoboxData();
    });
    var filteredAccountTypesUpdateHandler = zemDataFilterService.onFilteredAccountTypesUpdate(function () {
        getDailyStats();
        $scope.getInfoboxData();
    });
    var filteredStatusesUpdateHandler = zemDataFilterService.onFilteredStatusesUpdate(getDailyStats);
    $scope.$on('$destroy', function () {
        filteredSourcesUpdateHandler();
        filteredAgenciesUpdateHandler();
        filteredAccountTypesUpdateHandler();
        filteredStatusesUpdateHandler();
    });

    function initChartMetricsFromLocalStorage () {
        var chartMetrics = zemChartStorageService.loadMetrics(constants.level.ALL_ACCOUNTS);
        if (chartMetrics) {
            $scope.chartMetric1 = chartMetrics.metric1;
            $scope.chartMetric2 = chartMetrics.metric2;
        }
    }

    $scope.init = function () {
        setChartOptions();
        initChartMetricsFromLocalStorage();

        getDailyStats();
        $scope.getInfoboxData();

        $scope.setActiveTab();

        var activeEntityUpdateHandler = zemNavigationNewService.onActiveEntityChange(initChartMetricsFromLocalStorage);
        $scope.$on('$destroy', activeEntityUpdateHandler);
    };

    $scope.init();
});
