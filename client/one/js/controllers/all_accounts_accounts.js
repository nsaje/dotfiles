/*globals angular,moment,constants,options*/
angular.module('one.legacy').controller('AllAccountsAccountsCtrl', function ($scope, $state, $timeout, api, zemAccountService, zemFilterService, zemPostclickMetricsService, zemUserSettings, zemNavigationService, zemDataFilterService, zemGridConstants, zemPermissions) { // eslint-disable-line max-len
    $scope.requestInProgress = false;
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.chartMetric.COST;
    $scope.chartMetric2 = constants.chartMetric.CLICKS;
    $scope.chartMetricOptions = options.allAccountsChartMetrics;
    $scope.chartData = undefined;
    $scope.chartHidden = false;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.chartIsLoading = false;
    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.localStoragePrefix = 'allAccountsAccounts';

    $scope.selection = {
        entityIds: [],
        totals: true,
    };
    $scope.grid = {
        api: undefined,
        level: constants.level.ALL_ACCOUNTS,
        breakdown: constants.breakdown.ACCOUNT,
    };
    if (!$scope.hasPermission('zemauth.bulk_actions_on_all_levels')) {
        $scope.grid.options = {};
    }

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

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

                $state.go('main.accounts.settings', {id: data.id});
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

        dailyStatsPromise = api.dailyStats.list($scope.level, null, $scope.grid.breakdown, dateRange.startDate, dateRange.endDate, convertedSelection, true, getDailyStatsMetrics());
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
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            getDailyStats();
        }
    });

    if (zemPermissions.hasPermission('zemauth.can_see_new_filter_selector')) {
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
    } else {
        $scope.$watch(zemFilterService.getShowArchived, function (newValue, oldValue) {
            if (newValue === oldValue) {
                return;
            }

            getDailyStats();
        });

        $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }

            getDailyStats();
        }, true);

        $scope.$watch(zemFilterService.getFilteredAgencies, function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            getDailyStats();
            $scope.getInfoboxData();
        }, true);

        $scope.$watch(zemFilterService.getFilteredAccountTypes, function (newValue, oldValue) {
            if (angular.equals(newValue, oldValue)) {
                return;
            }
            getDailyStats();
            $scope.getInfoboxData();
        }, true);
    }

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;
        $scope.chartBtnTitle = $scope.chartHidden ? 'Show chart' : 'Hide chart';

        $timeout(function () {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    $scope.init = function () {
        userSettings.registerWithoutWatch('chartMetric1');
        userSettings.registerWithoutWatch('chartMetric2');
        userSettings.registerGlobal('chartHidden');

        setChartOptions();

        getDailyStats();
        $scope.getInfoboxData();

        $scope.setActiveTab();
    };

    $scope.init();
});
