/*globals oneApp,moment,constants,options*/
oneApp.controller('AllAccountsAccountsCtrl', ['$scope', '$state', '$location', '$window', '$timeout', 'api', 'localStorageService', 'zemCustomTableColsService', 'zemPostclickMetricsService', 'zemChartService', function ($scope, $state, $location, $window, $timeout, api, localStorageService, zemCustomTableColsService, zemPostclickMetricsService, zemChartService) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.requestInProgress = false;
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.chartMetric.COST;
    $scope.chartMetric2 = constants.chartMetric.CLICKS;
    $scope.chartMetricOptions = options.allAccountsChartMetrics;
    $scope.chartData = undefined;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-cost';
    $scope.sizeRange = [5, 10, 20, 50];
    $scope.pagination = {
        currentPage: 1,
    };
    $scope.columns = [
        {
            name: 'Account',
            field: 'name_link',
            unselectable: true,
            checked: true,
            type: 'linkText',
            hasTotalsLabel: true,
            totalRow: false,
            help: 'A partner account.',
            order: true,
            orderField: 'name',
            initialOrder: 'asc'
        },
        {
            name: 'Status',
            field: 'status_label',
            unselectable: true,
            checked: true,
            type: 'text',
            totalRow: false,
            help: 'Status of an account (enabled or paused). An account is paused only if all its campaigns are paused too; otherwise the account is enabled.',
            extraThCss: 'text-center',
            extraTdCss: 'text-center',
            order: true,
            orderField: 'status',
            initialOrder: 'asc'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
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
            help: 'The number of times a content ad has been clicked.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Last OK Sync',
            field: 'last_sync',
            checked: false,
            type: 'datetime',
            help: 'Dashboard reporting data is synchronized on an hourly basis. This is when the most recent synchronization occurred.',
            order: true,
            initialOrder: 'desc'
        }
    ];

    var initColumns = function () {
        var cols;

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            zemPostclickMetricsService.insertColumns($scope.columns, $scope.isPermissionInternal('zemauth.postclick_metrics'));
        }

        cols = zemCustomTableColsService.load('allAccountsAccountsCols', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('allAccountsAccountsCols', newValue);
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

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.postclick_metrics')
            );
        }
    };

    var getDailyStats = function () {
        api.dailyStats.list('all_accounts', null, $scope.dateRange.startDate, $scope.dateRange.endDate, null, true, [$scope.chartMetric1, $scope.chartMetric2]).then(
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

        $location.search('order', $scope.order);
        localStorageService.set('allAccountsAccounts.order', $scope.order);
        getTableData();
    };

    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.accountAccountsTable.get($scope.pagination.currentPage, $scope.pagination.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.order = data.order;
                $scope.pagination = data.pagination;

                $scope.rows = $scope.rows.map(function (x) {
                    x.name_link = {
                        text: x.name,
                        url: $state.href($scope.getDefaultAccountState(), {id: x.id})
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
            $location.search('chart_metric1', $scope.chartMetric1);
            localStorageService.set('allAccountsAccounts.chartMetric1', $scope.chartMetric1);
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
            $location.search('chart_metric2', $scope.chartMetric2);
            localStorageService.set('allAccountsAccounts.chartMetric2', $scope.chartMetric2);
        }
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

    var loadPage = function(page) {
        if(page && page > 0 && page <= $scope.pagination.numPages) {
            $scope.pagination.currentPage = page;
        }

        if ($scope.pagination.currentPage && $scope.pagination.size) {
            $location.search('page', $scope.pagination.currentPage);

            getTableData();
        }
    };

    $scope.changePaginationSize = function() {
        // Here we use additional scope variable pagination.sizeTemp
        // to allow repeated selection of already selected options
        $scope.pagination.size = $scope.pagination.sizeTemp;
        $scope.pagination.sizeTemp = '';

        $location.search('size', $scope.pagination.size);
        localStorageService.set('allAccountsAccounts.paginationSize', $scope.pagination.size);
        loadPage();
    };

    $scope.toggleChart = function () {
        $scope.isChartShown = !$scope.isChartShown;
        $scope.chartBtnTitle = $scope.isChartShown ? 'Hide chart' : 'Show chart';
        $location.search('chart_hidden', !$scope.isChartShown ? '1' : null);
    };

    // export
    $scope.downloadReport = function() {
        $window.open('api/accounts/export/?type=' + $scope.exportType + '&start_date=' + $scope.dateRange.startDate.format() + '&end_date=' + $scope.dateRange.endDate.format(), '_blank');
        $scope.exportType = '';
    };

    $scope.init = function() {
        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get('allAccountsAccounts.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get('allAccountsAccounts.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;
        var size = $location.search().size || localStorageService.get('allAccountsAccounts.paginationSize') || $scope.sizeRange[0];
        var page = $location.search().page;
        var order = $location.search().order || localStorageService.get('allAccountsAccounts.order') || $scope.order;

        setChartOptions();

        if (chartMetric1 !== undefined && $scope.chartMetric1 !== chartMetric1) {
            $scope.chartMetric1 = chartMetric1;
            $location.search('chart_metric1', chartMetric1);
        }

        if (chartMetric2 !== undefined && $scope.chartMetric2 !== chartMetric2) {
            $scope.chartMetric2 = chartMetric2;
            $location.search('chart_metric2', chartMetric2);
        }

        if (chartHidden) {
            $scope.isChartShown = false;
        }

        if (order !== undefined && $scope.order !== order) {
            $scope.order = order;
            $location.search('order', order);
        }

        pollSyncStatus();

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
        }

        if (size !== undefined && $scope.pagination.size !== size) {
            $scope.pagination.size = size;
        }
        
        loadPage();
        getDailyStats();
        initColumns();
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('chart_metric1', null);
        $location.search('chart_metric2', null);
        $location.search('page', null);
        $location.search('size', null);
        $location.search('order', null);
    });

    $scope.init();
}]);
