/*globals oneApp,moment,constants,options*/
oneApp.controller('AllAccountsAccountsCtrl', ['$scope', '$state', '$location', '$timeout', 'api', 'zemCustomTableColsService', 'zemFilterService', 'zemPostclickMetricsService', 'zemUserSettings', function ($scope, $state, $location, $timeout, api, zemCustomTableColsService, zemFilterService, zemPostclickMetricsService, zemUserSettings) {
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
    $scope.pagination = {
        currentPage: 1,
    };

    var userSettings = zemUserSettings.getInstance($scope, 'allAccountsAccounts');

    $scope.exportOptions = [
        {name: 'By Day (CSV)', value: 'csv'},
        {name: 'By Day (Excel)', value: 'excel'}
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
            shown: true,
            help: "Amount spent per account",
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: "The average CPC.",
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
               'clicks', 'cost', 'cpc', 'budget', 'available_budget', 'unspent_budget'
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

    $scope.setAccount(null);
    $scope.setCampaign(null);
    $scope.setAdGroup(null);

    var initColumns = function () {
        var cols;

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

        cols = zemCustomTableColsService.load('allAccountsAccounts', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('allAccountsAccounts', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.addAccount = function () {
        $scope.requestInProgress = true;

        api.account.create().then(
            function (data) {
                $scope.accounts.push({
                    'name': data.name,
                    'id': data.id,
                    'campaigns': []
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

        if (values.indexOf($scope.chartMetric1) === -1) {
            $scope.chartMetric1 = constants.chartMetric.CLICKS;
        }

        if ($scope.chartMetric2 !== 'none' && values.indexOf($scope.chartMetric2) === -1) {
            $scope.chartMetric2 = constants.chartMetric.COST;
        }

        return [$scope.chartMetric1, $scope.chartMetric2];
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

    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if(newValue === true && oldValue === false){
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

    var pollSyncStatus = function() {
        if($scope.isSyncInProgress){
            $timeout(function() {
                api.checkAccountsSyncProgress.get().then(
                    function(data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if($scope.isSyncInProgress == false){
                            // we found out that the sync is no longer in progress
                            // time to reload the data
                            getTableData();
                            getDailyStats();
                        }
                    },
                    function(data) {
                        // error
                        $scope.isSyncInProgress = false;
                    }
                ).finally(function() {
                    pollSyncStatus();
                });
            }, 5000);
        }
    };

    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;
        api.accountSync.get();
    };

    $scope.loadPage = function(page) {
        if(page && page > 0 && page <= $scope.pagination.numPages) {
            $scope.pagination.currentPage = page;
        }

        if ($scope.pagination.currentPage && $scope.pagination.size) {
            $location.search('page', $scope.pagination.currentPage);

            getTableData();
        }
    };

    $scope.$watch('size', function(newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.loadPage();
        }
    });

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;
        $scope.chartBtnTitle = $scope.chartHidden ? 'Show chart' : 'Hide chart';

        $timeout(function() {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    $scope.init = function() {
        var page = parseInt($location.search().page || '1');

        userSettings.register('chartMetric1');
        userSettings.register('chartMetric2');
        userSettings.register('order');
        userSettings.register('size');
        userSettings.registerGlobal('chartHidden');

        setChartOptions();

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
        }

        $scope.loadPage();
        getDailyStats();
        getTableData();
        initColumns();
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('page', null);
    });

    $scope.init();
}]);
