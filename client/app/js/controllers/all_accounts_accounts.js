/*globals oneApp,moment,constants,options*/
oneApp.controller('AllAccountsAccountsCtrl', ['$scope', '$state', '$location', '$window', '$timeout', 'api', 'localStorageService', 'zemCustomTableColsService', 'zemChartService', function ($scope, $state, $location, $window, $timeout, api, localStorageService, zemCustomTableColsService, zemChartService) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.requestInProgress = false;
    $scope.selectedSourceIds = [];
    $scope.selectedSourceTotals = true;
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.sourceChartMetric.CLICKS;
    $scope.chartMetric2 = null;
    $scope.dailyStats = [];
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
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            help: "Amount spent per account"
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            help: "The average CPC."
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
            help: 'The number of times a content ad has been clicked.'
        },
        {
            name: 'Last OK Sync',
            field: 'last_sync',
            checked: false,
            type: 'datetime',
            help: 'Dashboard reporting data is synchronized on an hourly basis. This is when the most recent synchronization occurred.'
        }
    ];

    $scope.initColumns = function () {
        var cols;

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

    $scope.setChartData = function () {
        var result = {
            formats: [],
            data: [],
            names: [],
            ids: []
        };

        result.formats = [$scope.chartMetric1, $scope.chartMetric2].map(function (x) {
            var format = null;
            if (x === constants.sourceChartMetric.COST ||
                x === constants.sourceChartMetric.CPC) {
                format = 'currency';
            } else if (x === constants.sourceChartMetric.CTR) {
                format = 'percent';
            }

            return format;
        });

        var temp = {};
        var lastDate = null;
        var oneDayMs = 24*60*60*1000;
        $scope.dailyStats.forEach(function (stat) {
            if (!temp.hasOwnProperty(stat.sourceId)) {
                temp[stat.sourceId] = {
                    name: stat.sourceName,
                    id: stat.sourceId,
                    data: [[]]
                };
            }

            // insert nulls for missing values
            if (lastDate) {
                for (var date = lastDate; date < stat.date - oneDayMs; date += oneDayMs) {
                    data[0].push([date, null]);

                    if (data[1]) {
                        data[1].push([date, null]);
                    }
                }
            }
            lastDate = stat.date;

            temp[stat.sourceId].data[0].push([stat.date, stat[$scope.chartMetric1]]);

            if ($scope.chartMetric2 && $scope.chartMetric2 !== $scope.chartMetric1) {
                if (!temp[stat.sourceId].data[1]) {
                    temp[stat.sourceId].data[1] = [];
                }
                temp[stat.sourceId].data[1].push([stat.date, stat[$scope.chartMetric2]]);
            }
        });

        Object.keys(temp).forEach(function (sourceId) {
            result.data.push(temp[sourceId].data);
            result.names.push(temp[sourceId].name);
            result.ids.push(temp[sourceId].id);
        });

        $scope.chartData = result;
    };

    $scope.getDailyStats = function () {
        api.accountDailyStats.list($scope.dateRange.startDate, $scope.dateRange.endDate).then(
            function (data) {
                $scope.dailyStats = data;
                $scope.setChartData();
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.orderRows = function (col) {
        if ($scope.order.indexOf(col) === 1) {
            $scope.order = col;
        } else if ($scope.order.indexOf(col) === -1 && col === 'name') {
            $scope.order = col;
        } else {
            $scope.order = '-' + col;
        }

        $location.search('order', $scope.order);
        $scope.getTableData();
    };

    $scope.getTableData = function (showWaiting) {
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
        $scope.getDailyStats();
        $scope.getTableData();
    });

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.setChartData();
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
            $scope.setChartData();
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
                            $scope.getTableData();
                            $scope.getDailyStats();
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

            $scope.getTableData();
        }
    };

    $scope.changePaginationSize = function() {
        // Here we use additional scope variable pagination.sizeTemp
        // to allow repeated selection of already selected options
        $scope.pagination.size = $scope.pagination.sizeTemp;
        $scope.pagination.sizeTemp = '';

        $location.search('size', $scope.pagination.size);
        localStorageService.set('allAccountsAccounts.paginationSize', $scope.pagination.size);
        $scope.loadPage();
    };

    $scope.toggleChart = function () {
        $scope.isChartShown = !$scope.isChartShown;
        $scope.chartBtnTitle = $scope.isChartShown ? 'Hide chart' : 'Show chart';
        $location.search('chart_hidden', !$scope.isChartShown ? '1' : null);
    };

    $scope.init = function() {
        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get('allAccountsAccounts.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get('allAccountsAccounts.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;
        var size = $location.search().size || localStorageService.get('allAccountsAccounts.paginationSize') || $scope.sizeRange[0];
        var page = $location.search().page;
        var changed = false;
        var tableChanged = false;

        if (chartMetric1 !== undefined && $scope.chartMetric1 !== chartMetric1) {
            $scope.chartMetric1 = chartMetric1;
            $location.search('chart_metric1', chartMetric1);
            changed = true;
        }

        if (chartMetric2 !== undefined && $scope.chartMetric2 !== chartMetric2) {
            $scope.chartMetric2 = chartMetric2;
            $location.search('chart_metric2', chartMetric2);
            changed = true;
        }

        if (chartHidden) {
            $scope.isChartShown = false;
        }

        if (changed) {
            $scope.setChartData();
        }

        $scope.order = $location.search().order || $scope.order;

        $scope.initColumns();

        pollSyncStatus();

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
            tableChanged = true;
        }

        if (size !== undefined && $scope.pagination.size !== size) {
            $scope.pagination.size = size;
            tableChanged = true;
        }
        
        if (tableChanged) {
            $scope.loadPage();
        }
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('chart_metric1', null);
        $location.search('chart_metric2', null);
        $location.search('page', null);
        $location.search('size', null);
    });

    $scope.init();
}]);
