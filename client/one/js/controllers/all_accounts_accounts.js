/*globals angular,oneApp,moment,constants,options*/
oneApp.controller('AllAccountsAccountsCtrl', ['$scope', '$state', '$location', '$timeout', 'api', 'zemFilterService', 'zemPostclickMetricsService', 'zemUserSettings', 'zemNavigationService', function ($scope, $state, $location, $timeout, api, zemFilterService, zemPostclickMetricsService, zemUserSettings, zemNavigationService) { // eslint-disable-line max-len
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
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.pagination = {
        currentPage: 1,
    };
    $scope.localStoragePrefix = 'allAccountsAccounts';

    $scope.grid = {
        api: undefined,
        level: constants.level.ALL_ACCOUNTS,
        breakdown: constants.breakdown.ACCOUNT,
    };

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    $scope.exportOptions = [
      {name: 'By All Accounts (totals)', value: constants.exportType.ALL_ACCOUNTS},
      {name: 'Current View', value: constants.exportType.ACCOUNT, defaultOption: true},
      {name: 'By Campaign', value: constants.exportType.CAMPAIGN},
      {name: 'By Ad Group', value: constants.exportType.AD_GROUP},
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
            name: 'Agency',
            field: 'agency',
            unselectable: true,
            checked: true,
            type: 'text',
            totalRow: false,
            help: 'Agency to which this account belongs.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_account_agency_information'),
            shown: $scope.hasPermission('zemauth.can_view_account_agency_information')
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
            name: 'Account Manager',
            field: 'default_account_manager',
            checked: false,
            type: 'text',
            totalRow: false,
            help: 'Account manager responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_managers_in_accounts_table'),
            shown: $scope.hasPermission('zemauth.can_see_managers_in_accounts_table')
        },
        {
            name: 'Sales Representative',
            field: 'default_sales_representative',
            checked: false,
            type: 'text',
            totalRow: false,
            help: 'Sales representative responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_managers_in_accounts_table'),
            shown: $scope.hasPermission('zemauth.can_see_managers_in_accounts_table')
        },
        {
            name: 'Account Type',
            field: 'account_type',
            checked: false,
            type: 'text',
            totalRow: false,
            help: 'Type of account.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_account_type'),
            shown: $scope.hasPermission('zemauth.can_see_account_type')
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
            internal: $scope.isPermissionInternal('zemauth.can_view_platform_cost_breakdown'),
            shown: $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
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
            internal: $scope.isPermissionInternal('zemauth.can_view_platform_cost_breakdown'),
            shown: $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
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
            internal: $scope.isPermissionInternal('zemauth.can_view_platform_cost_breakdown'),
            shown: $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
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
            shown: $scope.hasPermission('zemauth.can_view_flat_fees') &&
                $scope.hasPermission('zemauth.can_view_platform_cost_breakdown'),
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
            shown: $scope.hasPermission('zemauth.can_view_flat_fees') &&
                $scope.hasPermission('zemauth.can_view_platform_cost_breakdown'),
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
            internal: false,
            shown: true,
        },
        {
            name: 'Margin',
            field: 'margin',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Agency\'s margin',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_agency_margin'),
            shown: $scope.hasPermission('zemauth.can_view_agency_margin')
        },
        {
            name: 'Total Spend + Margin',
            field: 'agency_total',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: 'Total billing cost including Media Spend, License Fee and Agency Margin',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_agency_margin'),
            shown: $scope.hasPermission('zemauth.can_view_agency_margin')
        },
        {
            name: 'Media budgets',
            field: 'allocated_budgets',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_projections'),
            shown: $scope.hasPermission('zemauth.can_see_projections') &&
                $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
        },
        {
            name: 'Pacing',
            field: 'pacing',
            checked: false,
            type: 'percent',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_projections'),
            shown: $scope.hasPermission('zemauth.can_see_projections') &&
                $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
        },
        {
            name: 'Spend Projection',
            field: 'spend_projection',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_projections'),
            shown: $scope.hasPermission('zemauth.can_see_projections') &&
                $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
        },
        {
            name: 'License Fee Projection',
            field: 'license_fee_projection',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_projections'),
            shown: $scope.hasPermission('zemauth.can_see_projections') &&
                $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
        },
        {
            name: 'Total Fee Projection',
            field: 'total_fee_projection',
            checked: false,
            type: 'currency',
            totalRow: true,
            help: '',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_projections'),
            shown: $scope.hasPermission('zemauth.can_see_projections') &&
                $scope.hasPermission('zemauth.can_view_platform_cost_breakdown') &&
                $scope.hasPermission('zemauth.can_view_flat_fees')
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
            name: 'Avg. CPM',
            field: 'cpm',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            help: 'The average CPM.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
            shown: $scope.hasPermission('zemauth.can_view_new_columns'),
            internal: $scope.isPermissionInternal('zemauth.can_view_new_columns'),
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
            name: 'CTR',
            field: 'ctr',
            checked: true,
            type: 'percent',
            shown: true,
            defaultValue: '0.0%',
            totalRow: true,
            help: 'The number of clicks divided by the number of impressions.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: '',
            nameCssClass: 'data-status-icon',
            type: 'dataStatus',
            internal: $scope.isPermissionInternal('zemauth.data_status_column'),
            shown: false,
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
            shown: false,
            help: 'Dashboard reporting data is synchronized on an hourly basis. This is when the most recent synchronization occurred (in Eastern Standard Time).',
            order: true,
            initialOrder: 'desc'
        }
    ];

    $scope.columnCategories = [
        {
            'name': 'Costs',
            fields: [
                'data_cost', 'media_cost', 'e_media_cost', 'e_data_cost',
                'license_fee', 'total_fee', 'flat_fee',
                'billing_cost', 'margin', 'agency_total',
            ],
        },
        {
            'name': 'Projections',
            fields: [
                'total_fee_projection', 'license_fee_projection', 'spend_projection',
                'pacing', 'allocated_budgets',
            ],
        },
        {
            'name': 'Traffic Acquisition',
            'fields': [
                'clicks', 'impressions', 'ctr', 'cpc', 'cpm',
            ]
        },
        {
            'name': 'Audience Metrics',
            'fields': [
                'visits', 'unique_users', 'returning_users', 'pageviews', 'percent_new_users',
                'bounce_rate', 'pv_per_visit', 'avg_tos', 'click_discrepancy', 'unique_users',
                'returning_users', 'bounced_visits',
            ]
        },
        {
            'name': 'Management',
            'fields': [
                'default_account_manager', 'default_sales_representative', 'account_type'
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

        zemPostclickMetricsService.insertUserColumns(
            $scope.columns,
            $scope.columns.length - 2,
            $scope.hasPermission('zemauth.can_view_new_columns'),
            $scope.isPermissionInternal('zemauth.can_view_new_columns')
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

    $scope.getInfoboxData = function () {
        api.allAccountsOverview.get($scope.dateRange.startDate, $scope.dateRange.endDate).then(
            function (data) {
                $scope.infoboxHeader = data.header;
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
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
            $scope.reflowGraph(1);
        });
    };

    // From parent scope (mainCtrl).
    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
            return;
        }

        $scope.getInfoboxData();
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

    $scope.$watch(zemFilterService.getShowArchived, function (newValue, oldValue) {
        if (newValue === oldValue) {
            return;
        }

        getTableData();
        getDailyStats();
    });

    $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        getTableData();
        getDailyStats();
    }, true);

    $scope.$watch(zemFilterService.getFilteredAgencies, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }
        getTableData();
        getDailyStats();
        $scope.getInfoboxData();
        // TODO: Breakdowns
    }, true);

    $scope.$watch(zemFilterService.getFilteredAccountTypes, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }
        getTableData();
        getDailyStats();
        $scope.getInfoboxData();
        // TODO: Breakdowns
    }, true);

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
        $scope.getInfoboxData();
        getTableData();
        initColumns();
    };

    $scope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
        $location.search('page', null);
    });

    $scope.init();
}]);
