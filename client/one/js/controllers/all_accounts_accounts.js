/*globals oneApp,moment,constants,options*/
oneApp.controller('AllAccountsAccountsCtrl', ['$scope', '$state', '$location', '$timeout', 'api', 'zemFilterService', 'zemPostclickMetricsService', 'zemUserSettings', 'zemNavigationService', function ($scope, $state, $location, $timeout, api, zemFilterService, zemPostclickMetricsService, zemUserSettings, zemNavigationService) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.requestInProgress = false;
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.chartMetric.COST;
    $scope.chartMetric2 = constants.chartMetric.CLICKS;
    $scope.chartMetricOptions = options.allAccountsChartMetrics;
    $scope.chartData = undefined;
    $scope.chartHidden = false;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-cost';
    $scope.sizeRange = [5, 10, 20, 50];
    $scope.size = $scope.sizeRange[0];
    $scope.isIncompletePostclickMetrics = false;
    $scope.infoboxHeader = null;
    $scope.infoboxSettings = null;
    $scope.pagination = {
        currentPage: 1,
    };
    $scope.localStoragePrefix = 'allAccountsAccounts';

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    $scope.exportOptions = [
           {name: 'By Day (CSV)', value: 'csv'},
           {name: 'By Day (Excel)', value: 'excel'}
    ];

    $scope.exportPlusOptions = [
      {name: 'Current View', value: 'account-csv'},
      {name: 'By Campaign', value: 'campaign-csv'},
      {name: 'By Ad Group', value: 'adgroup-csv'}
    ];

    $scope.columns = [
        {
            name: 'Account',
            field: 'name_link',
            unselectable: true,
            checked: true,
            type: 'linkNav',
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'A partner account.',
            order: true,
            orderField: 'name',
            initialOrder: 'asc'
        },
        {
            name: 'Status',
            field: 'status',
            unselectable: true,
            checked: true,
            type: 'text',
            shown: true,
            totalRow: false,
            help: 'Status of an account (enabled or paused). An account is paused only if all its campaigns are paused too; otherwise the account is enabled.',
            order: true,
            orderField: 'status',
            initialOrder: 'asc'
        },
        {
            name: 'Total Budget',
            field: 'budget',
            checked: true,
            type: 'currency',
            totalRow: true,
            help: 'Total amount of allocated budget.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.all_accounts_budget_view'),
            shown: $scope.hasPermission('zemauth.all_accounts_budget_view')
        },
        {
            name: 'Available Budget',
            field: 'available_budget',
            checked: true,
            type: 'currency',
            totalRow: true,
            help: 'Total amount of budget still available.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.all_accounts_budget_view'),
            shown: $scope.hasPermission('zemauth.all_accounts_budget_view')
        },
        {
            name: 'Unspent Budget',
            field: 'unspent_budget',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Total budget minus the spend within the date range.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.unspent_budget_view'),
            shown: $scope.hasPermission('zemauth.unspent_budget_view')
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            help: 'Amount spent per account',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
            shown: !$scope.hasPermission('zemauth.can_view_effective_costs') && !$scope.hasPermission('zemauth.can_view_actual_costs')
        },
        {
            name: 'Actual Media Spend',
            field: 'media_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Amount spent per media source, including overspend.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_actual_costs'),
            shown: $scope.hasPermission('zemauth.can_view_actual_costs')
        },
        {
            name: 'Media Spend',
            field: 'e_media_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Amount spent per media source.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_effective_costs'),
            shown: $scope.hasPermission('zemauth.can_view_effective_costs')
        },
        {
            name: 'Actual Data Cost',
            field: 'data_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Additional targeting/segmenting costs, including overspend.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_actual_costs'),
            shown: $scope.hasPermission('zemauth.can_view_actual_costs')
        },
        {
            name: 'Data Cost',
            field: 'e_data_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Additional targeting/segmenting costs.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_effective_costs'),
            shown: $scope.hasPermission('zemauth.can_view_effective_costs')
        },
        {
            name: 'Actual Total Spend',
            field: 'total_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Sum of media spend, data cost and license fee, including overspend.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_actual_costs'),
            shown: $scope.hasPermission('zemauth.can_view_actual_costs')
        },
        {
            name: 'Total Spend',
            field: 'billing_cost',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Sum of media spend, data cost and license fee.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_effective_costs'),
            shown: $scope.hasPermission('zemauth.can_view_effective_costs')
        },
        {
            name: 'License Fee',
            field: 'license_fee',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Zemanta One platform usage cost.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_effective_costs'),
            shown: $scope.hasPermission('zemauth.can_view_effective_costs')
        },
        {
            name: 'Recognized Flat Fee',
            field: 'flat_fee',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_flat_fees'),
            shown: $scope.hasPermission('zemauth.can_view_flat_fees')
        },
        {
            name: 'Total Fee',
            field: 'total_fee',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_flat_fees'),
            shown: $scope.hasPermission('zemauth.can_view_flat_fees')
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'The average CPC.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
            shown: true,
            help: 'The number of times a content ad has been clicked.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number',
            shown: true,
            totalRow: true,
            help: 'The number of times content ads have been displayed.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: '',
            nameCssClass: 'data-status-icon',
            type: 'dataStatus',
            internal: $scope.isPermissionInternal('zemauth.data_status_column'),
            shown: $scope.hasPermission('zemauth.data_status_column'),
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'Status of third party data accuracy.',
            disabled: false
        },
        {
            name: 'Last OK Sync (EST)',
            field: 'last_sync',
            checked: false,
            type: 'datetime',
            shown: true,
            help: 'Dashboard reporting data is synchronized on an hourly basis. This is when the most recent synchronization occurred (in Eastern Standard Time).',
            order: true,
            initialOrder: 'desc'
        }
    ];

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
                'clicks', 'impressions', 'cost', 'data_cost', 'cpc', 'budget',
                'available_budget', 'unspent_budget',
                'media_cost', 'e_media_cost', 'e_data_cost', 'total_cost', 'billing_cost',
                'license_fee', 'total_fee', 'flat_fee'
            ]
        },
        {
            'name': 'Audience Metrics',
            'fields': [
                'visits', 'pageviews', 'percent_new_users',
                'bounce_rate', 'pv_per_visit', 'avg_tos',
                'click_discrepancy'
            ]
        },
        {
            'name': 'Data Sync',
            'fields': ['last_sync']
        }
    ];

    $scope.setModels(null);

    var initColumns = function () {
        zemPostclickMetricsService.insertAcquisitionColumns(
            $scope.columns,
            $scope.columns.length - 2,
            $scope.hasPermission('zemauth.aggregate_postclick_acquisition'),
            $scope.isPermissionInternal('zemauth.aggregate_postclick_acquisition')
        );

        zemPostclickMetricsService.insertEngagementColumns(
            $scope.columns,
            $scope.columns.length - 2,
            $scope.hasPermission('zemauth.aggregate_postclick_engagement'),
            $scope.isPermissionInternal('zemauth.aggregate_postclick_engagement')
        );
    };

    $scope.addAccount = function () {
        $scope.requestInProgress = true;

        api.account.create().then(
            function (data) {
                zemNavigationService.addAccountToCache({
                    'name': data.name,
                    'id': data.id,
                    'campaigns': [],
                });

                $state.go('main.accounts.agency', {id: data.id});
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

        if ($scope.hasPermission('zemauth.can_view_effective_costs')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                options.effectiveCostChartMetrics,
                $scope.isPermissionInternal('zemauth.can_view_effective_costs')
            );
        } else if (!$scope.hasPermission('zemauth.can_view_actual_costs')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                options.legacyCostChartMetrics,
                false
            );
        }
        if ($scope.hasPermission('zemauth.can_view_actual_costs')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                options.actualCostChartMetrics,
                $scope.isPermissionInternal('zemauth.can_view_actual_costs')
            );
        }
    };

    var getDailyStats = function () {
        api.dailyStats.list($scope.level, null, $scope.dateRange.startDate, $scope.dateRange.endDate, null, true, getDailyStatsMetrics(), null).then(
            function (data) {
                setChartOptions();
                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    var getInfoboxData = function () {
        if (!$scope.hasPermission('zemauth.can_see_infobox')) {
            return;
        }

        api.allAccountsOverview.get().then(
            function (data) {
                $scope.infoboxHeader = data.header;
                $scope.infoboxSettings = data.settings;
            }
        );
    };

    $scope.orderRows = function (order) {
        $scope.order = order;
        getTableData();
    };

    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.accountAccountsTable.get($scope.pagination.currentPage, $scope.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.dataStatus = data.dataStatus;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.order = data.order;
                $scope.pagination = data.pagination;

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;

                $scope.rows = $scope.rows.map(function (x) {
                    x.name_link = {
                        text: x.name,
                        state: $scope.getDefaultAccountState(),
                        id: x.id
                    };

                    return x;
                });

                $location.search('page', $scope.pagination.currentPage);
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };

    // From parent scope (mainCtrl).
    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
            return;
        }

        getDailyStats();
        getTableData();
    });

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            getDailyStats();
        }
    });

    $scope.$watch('isSyncInProgress', function (newValue, oldValue) {
        if (newValue === true && oldValue === false) {
            pollSyncStatus();
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            getDailyStats();
        }
    });

    $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        getTableData();
        getDailyStats();
    }, true);

    $scope.$watch(zemFilterService.getShowArchived, function (newValue, oldValue) {
        if (newValue === oldValue) {
            return;
        }

        getTableData();
    });

    var pollSyncStatus = function () {
        if ($scope.isSyncInProgress) {
            $timeout(function () {
                api.checkAccountsSyncProgress.get().then(
                    function (data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if ($scope.isSyncInProgress == false) {
                            // we found out that the sync is no longer in progress
                            // time to reload the data
                            getTableData();
                            getDailyStats();
                        }
                    },
                    function (data) {
                        // error
                        $scope.isSyncInProgress = false;
                    }
                ).finally(function () {
                    pollSyncStatus();
                });
            }, 5000);
        }
    };

    $scope.triggerSync = function () {
        $scope.isSyncInProgress = true;
        api.accountSync.get();
    };

    $scope.loadPage = function (page) {
        if (page && page > 0 && page <= $scope.pagination.numPages) {
            $scope.pagination.currentPage = page;
        }

        if ($scope.pagination.currentPage && $scope.pagination.size) {
            $location.search('page', $scope.pagination.currentPage);

            getTableData();
        }
    };

    $scope.$watch('size', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.loadPage();
        }
    });

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;
        $scope.chartBtnTitle = $scope.chartHidden ? 'Show chart' : 'Hide chart';

        $timeout(function () {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    $scope.init = function () {
        var page = parseInt($location.search().page || '1');
        var size = parseInt($location.search().size || '0');

        userSettings.registerWithoutWatch('chartMetric1');
        userSettings.registerWithoutWatch('chartMetric2');
        userSettings.register('order');
        userSettings.register('size');
        userSettings.registerGlobal('chartHidden');

        if (size !== 0 && $scope.size !== size) {
            $scope.size = size;
        }
        // if nothing in local storage or page query var set first as default
        if ($scope.size === 0) {
            $scope.size = $scope.sizeRange[0];
        }

        setChartOptions();

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
        }

        $scope.loadPage();
        getDailyStats();
        getTableData();
        initColumns();
    };

    $scope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
        $location.search('page', null);
    });

    $scope.init();
}]);
