/*globals oneApp,constants,moment*/
oneApp.controller('AccountCampaignsCtrl', ['$location', '$scope', '$state', '$timeout', 'api', 'localStorageService', 'zemCustomTableColsService', 'zemPostclickMetricsService', 'zemChartService', '$window', function ($location, $scope, $state, $timeout, api, localStorageService, zemCustomTableColsService, zemPostclickMetricsService, zemChartService, $window) {
    $scope.getTableDataRequestInProgress = false;
    $scope.addCampaignRequestInProgress = false;
    $scope.isSyncInProgress = false;
    $scope.isSyncRecent = true;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = options.accountChartMetrics;
    $scope.selectedCampaignIds = [];
    $scope.selectedTotals = true;
    $scope.rows = null;
    $scope.totalRow = null;
    $scope.order = '-cost';
    $scope.isIncompletePostclickMetrics = false;

    $scope.updateSelectedCampaigns = function (campaignId) {
        campaignId = campaignId.toString();

        var i = $scope.selectedCampaignIds.indexOf(campaignId);
        if (i > -1) {
            $scope.selectedCampaignIds.splice(i, 1);
        } else {
            $scope.selectedCampaignIds.push(campaignId);
        }

        $scope.columns[0].disabled = $scope.selectedCampaignIds.length >= 4;
    };

    $scope.selectedCampaignsChanged = function (row, checked) {
        if (row.campaign) {
            $scope.updateSelectedCampaigns(row.campaign);
        } else {
            $scope.selectedTotals = !$scope.selectedTotals;
        }

        $scope.updateSelectedRowsData();
    };

    $scope.updateSelectedRowsData = function () {
        if (!$scope.selectedTotals && !$scope.selectedCampaignIds.length) {
            $scope.selectedTotals = true;
            $scope.totalRow.checked = true;
        }

        $location.search('campaign_ids', $scope.selectedCampaignIds.join(','));
        $location.search('campaign_totals', $scope.selectedTotals ? 1 : null);

        getDailyStats();
    };

    $scope.selectRows = function () {
        $scope.totalRow.checked = $scope.selectedTotals;
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selectedCampaignIds.indexOf(x.campaign.toString()) > -1;
        });
    };

    $scope.columns = [
        {
            name: '',
            field: 'checked',
            type: 'checkbox',
            checked: true,
            totalRow: true,
            unselectable: true,
            order: false,
            selectCallback: $scope.selectedCampaignsChanged,
            disabled: false
        },
        {
            name: 'Campaign',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'linkNav',
            hasTotalsLabel: true,
            totalRow: false,
            help: 'Name of the campaign.',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'Status',
            field: 'state',
            checked: true,
            type: 'text',
            totalRow: false,
            help: 'Status of a campaign (enabled or paused). A campaign is paused only if all its ad groups are paused too; otherwise, the campaign is enabled.',
            extraThCss: 'text-center',
            extraTdCss: 'text-center',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            totalRow: true,
            help: 'The amount spent per campaign.',
            order: true,
            initialOrder: 'desc',
            isDefaultOrder: true
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            totalRow: true,
            help: 'The average CPC for each campaign.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
            totalRow: true,
            help: 'The number of times campaign\'s content ads have been clicked.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number',
            totalRow: true,
            help: 'The number of times campaign\'s content ads have been displayed.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'CTR',
            field: 'ctr',
            checked: true,
            type: 'percent',
            defaultValue: '0.0%',
            totalRow: true,
            help: 'The number of clicks divided by the number of impressions.',
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

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
               'cost', 'cpc', 'clicks', 'impressions', 'ctr',
               'budget', 'available_budget'
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

    $scope.addCampaign = function () {
        var accountId = $state.params.id;
        $scope.addCampaignRequestInProgress = true;

        api.accountCampaigns.create(accountId).then(
            function (data) {
                $scope.accounts.forEach(function (account) {
                    if (account.id.toString() === accountId.toString()) {
                        account.campaigns.push({
                            id: data.id,
                            name: data.name,
                            adGroups: []
                        });

                        $state.go('main.campaigns.agency', {id: data.id});
                    }
                });
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
            getDailyStats();
            $location.search('chart_metric1', $scope.chartMetric1);
            localStorageService.set('accountCampaigns.chartMetric1', $scope.chartMetric1);
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            getDailyStats();
            $location.search('chart_metric2', $scope.chartMetric2);
            localStorageService.set('accountCampaigns.chartMetric2', $scope.chartMetric2);
        }
    });

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.accountChartMetrics;

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.postclick_metrics')
            );
        }
    };

    var getDailyStats = function () {
        api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedCampaignIds, $scope.selectedTotals, [$scope.chartMetric1, $scope.chartMetric2]).then(
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

    $scope.selectedCampaignRemoved = function (id) {
        if (id !== 'totals') {
            $scope.updateSelectedCampaigns(id);
        } else {
            $scope.selectedTotals = false;
        }

        $scope.selectRows();
        $scope.updateSelectedRowsData();
    };

    var getTableData = function () {
        $scope.getTableDataRequestInProgress = true;

        api.accountCampaignsTable.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totalRow = data.totals;
                $scope.totalRow.checked = $scope.selectedTotals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.order = data.order;

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;

                $scope.rows = $scope.rows.map(function (x) {
                    x.name = {
                        text: x.name,
                        state: $scope.getDefaultCampaignState(),
                        id: x.campaign
                    };
                    x.state = x.state === constants.adGroupSettingsState.ACTIVE ? 'Active' : 'Paused';

                    return x;
                });

                $scope.selectRows();
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.getTableDataRequestInProgress = false;
        });
    };

    $scope.orderTableData = function(order) {
        $scope.order = order;

        $location.search('order', $scope.order);
        localStorageService.set('accountCampaigns.order', $scope.order);
        getTableData();
    };

    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;
        api.campaignSync.get(null, $state.params.id);
    };

    var pollSyncStatus = function() {
        if ($scope.isSyncInProgress){
            $timeout(function() {
                api.checkCampaignSyncProgress.get(null, $state.params.id).then(
                    function(data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if (!$scope.isSyncInProgress){
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

    $scope.toggleChart = function () {
        $scope.isChartShown = !$scope.isChartShown;
        $scope.chartBtnTitle = $scope.isChartShown ? 'Hide chart' : 'Show chart';
        $location.search('chart_hidden', !$scope.isChartShown ? '1' : null);

        $timeout(function() {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    $scope.$watch('isChartShown', function (newValue, oldValue) {
        zemChartService.save('zemChart', newValue);
    });

    var initColumns = function () {
        var cols;

        if ($scope.hasPermission('zemauth.all_accounts_budget_view')) {
            $scope.columns.splice(3, 0,
                {
                    name: 'Total Budget',
                    field: 'budget',
                    checked: true,
                    type: 'currency',
                    totalRow: true,
                    help: 'Total amount of allocated budget.',
                    order: true,
                    initialOrder: 'desc',
                    internal: $scope.isPermissionInternal('zemauth.all_accounts_budget_view')
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
                    internal: $scope.isPermissionInternal('zemauth.all_accounts_budget_view')
                }
            )
        }

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            zemPostclickMetricsService.insertColumns($scope.columns, $scope.isPermissionInternal('zemauth.postclick_metrics'));
        }

        cols = zemCustomTableColsService.load('accountCampaignsCols', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('accountCampaignsCols', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.init = function() {
        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get('accountCampaigns.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get('accountCampaigns.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;
        var order = $location.search().order || localStorageService.get('accountCampaigns.order') || $scope.order;

        var campaignIds = $location.search().campaign_ids;
        var campaignTotals = $location.search().campaign_totals;

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

        if (campaignIds) {
            campaignIds.split(',').forEach(function (id) {
                 $scope.updateSelectedCampaigns(id);
            });
            $location.search('campaign_ids', campaignIds);

            if ($scope.rows) {
                $scope.selectRows();
            }
        }

        $scope.selectedTotals = !$scope.selectedCampaignIds.length || !!campaignTotals;
        $location.search('campaign_totals', campaignTotals);

        if (order !== undefined && $scope.order !== order) {
            $scope.order = order;
            $location.search('order', order);
        }

        getTableData();
        initColumns();
        pollSyncStatus();
        getDailyStats();
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('campaign_ids', null);
        $location.search('campaign_totals', null);
        $location.search('chart_metric1', null);
        $location.search('chart_metric2', null);
    });

    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if(newValue === true && oldValue === false){
            pollSyncStatus();
        }
    });

    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
            return;
        }

        getTableData();
        getDailyStats();
    });

    $scope.downloadReport = function() {
        $window.open('api/accounts/' + $state.params.id + '/campaigns/export/?type=' + $scope.exportType + '&start_date=' + $scope.dateRange.startDate.format() + '&end_date=' + $scope.dateRange.endDate.format(), '_blank');
        $scope.exportType = '';
    };

    $scope.init();
}]);
