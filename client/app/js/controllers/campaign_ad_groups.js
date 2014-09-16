/*globals oneApp,moment,constants,options*/
oneApp.controller('CampaignAdGroupsCtrl', ['$location', '$scope', '$state', '$timeout', 'api', 'localStorageService', 'zemCustomTableColsService', 'zemChartService', function ($location, $scope, $state, $timeout, api, localStorageService, zemCustomTableColsService, zemChartService) {
    $scope.getTableDataRequestInProgress = false;
    $scope.addGroupRequestInProgress = false;
    $scope.isSyncInProgress = false;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = options.campaignChartMetrics;
    $scope.chartGoalMetrics = null;
    $scope.selectedAdGroupIds = [];
    $scope.selectedTotals = true;
    $scope.rows = null;
    $scope.totalRow = null;
    $scope.order = '-cost';

    $scope.updateSelectedAdGroups = function (adGroupId) {
        var i = $scope.selectedAdGroupIds.indexOf(adGroupId);
        if (i > -1) {
            $scope.selectedAdGroupIds.splice(i, 1);
        } else {
            $scope.selectedAdGroupIds.push(adGroupId);
        }

        $scope.columns[0].disabled = $scope.selectedAdGroupIds.length >= 4;
    };

    $scope.selectedAdGroupsChanged = function (row, checked) {
        if (row.ad_group) {
            $scope.updateSelectedAdGroups(row.ad_group);
        } else {
            $scope.selectedTotals = !$scope.selectedTotals;
        }

        $scope.updateSelectedRowsData();
    };

    $scope.updateSelectedRowsData = function () {
        if (!$scope.selectedTotals && !$scope.selectedAdGroupIds.length) {
            $scope.selectedTotals = true;
            $scope.totalRow.checked = true;
        }

        $location.search('ad_group_ids', $scope.selectedAdGroupIds.join(','));
        $location.search('ad_group_totals', $scope.selectedTotals ? 1 : null);

        // $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);
        // $scope.setAdGroupData('sourceTotals', $scope.selectedSourceTotals);

        $scope.getDailyStats();
    };

    $scope.selectRows = function () {
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selectedAdGroupIds.indexOf(x.ad_group) > -1;
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
            selectCallback: $scope.selectedAdGroupsChanged,
            disabled: false
        },
        {
            name: 'Name',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'linkText',
            hasTotalsLabel: true,
            totalRow: false,
            help: 'Name of the ad group.',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'State',
            field: 'state',
            checked: true,
            type: 'text',
            totalRow: false,
            help: 'Status of an ad group (enabled or paused).',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            totalRow: true,
            help: 'The amount spent per ad group.',
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
            help: 'The average CPC for each ad group.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
            totalRow: true,
            help: 'The number of times ad group\'s content ads have been clicked.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number',
            totalRow: true,
            help: 'The number of times ad group\'s content ads have been displayed.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'CTR',
            field: 'ctr',
            checked: true,
            type: 'percent',
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

    $scope.addAdGroup = function () {
        var campaignId = $state.params.id;
        $scope.addGroupRequestInProgress = true;

        api.campaignAdGroups.create(campaignId).then(
            function (data) {
                $scope.accounts.forEach(function (account) {
                    account.campaigns.forEach(function (campaign) {
                        if (campaign.id.toString() === campaignId.toString()) {
                            campaign.adGroups.push({
                                id: data.id,
                                name: data.name
                            });

                            $state.go('main.adGroups.settings', {id: data.id});
                        }
                    });
                });
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.addGroupRequestInProgress = false;
        });
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.getDailyStats();
            $location.search('chart_metric1', $scope.chartMetric1);
            localStorageService.set('campaignAdGroups.chartMetric1', $scope.chartMetric1);
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.getDailyStats();
            $location.search('chart_metric2', $scope.chartMetric2);
            localStorageService.set('campaignAdGroups.chartMetric2', $scope.chartMetric2);
        }
    });

    $scope.getDailyStats = function () {
        api.campaignDailyStats.list($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedAdGroupIds, $scope.selectedTotals, $scope.chartMetric1, $scope.chartMetric2).then(
            function (data) {
                $scope.chartGoalMetrics = data.goals;
                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.getTableData = function () {
        $scope.getTableDataRequestInProgress = true;

        api.campaignAdGroupsTable.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totalRow = data.totals;
                $scope.totalRow.checked = $scope.selectedTotals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.order = data.order;

                $scope.rows = $scope.rows.map(function (x) {
                    x.name = {
                        text: x.name,
                        url: $state.href($scope.getDefaultAdGroupState(), {id: x.ad_group})
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
        localStorageService.set('campaignAdGroups.order', $scope.order);
        $scope.getTableData();
    };

    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;
        api.campaignSync.get($state.params.id);
    };

    var pollSyncStatus = function() {
        if ($scope.isSyncInProgress){
            $timeout(function() {
                api.checkCampaignSyncProgress.get($state.params.id).then(
                    function(data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if (!$scope.isSyncInProgress){
                            // we found out that the sync is no longer in progress
                            // time to reload the data
                            $scope.getTableData();
                            /* $scope.getDailyStats(); */
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

    var initColumns = function () {
        var cols;

        cols = zemCustomTableColsService.load('campaignAdGroupsCols', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('campaignAdGroupsCols', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.init = function() {
        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get('campaignAdGroups.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get('campaignAdGroups.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;
        var order = $location.search().order || localStorageService.get('campaignAdGroups.order') || $scope.order;

        var data = $scope.adGroupData[$state.params.id];
        var adGroupIds = $location.search().ad_group_ids || (data && data.adGroupIds && data.adGroupIds.join(','));
        var adGroupTotals = $location.search().ad_group_totals || (data && data.adGroupTotals ? 1 : null);

        var tableChanged = false;

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

        if (adGroupIds) {
            $scope.selectedAdGroupIds = adGroupIds.split(',');
            $location.search('ad_group_ids', adGroupIds);

            if ($scope.rows) {
                $scope.selectRows();
            }
        }

        $scope.selectedTotals = !$scope.selectedAdGroupIds.length || !!adGroupTotals;
        $location.search('ad_group_totals', adGroupTotals);

        if (order !== undefined && $scope.order !== order) {
            $scope.order = order;
            $location.search('order', order);
            tableChanged = true;
        }

        if (tableChanged) {
            $scope.getTableData();
        }

        initColumns();

        pollSyncStatus();
        $scope.getDailyStats();
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('ad_group_ids', null);
        $location.search('ad_group_totals', null);
        $location.search('chart_metric1', null);
        $location.search('chart_metric2', null);
    });

    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if(newValue === true && oldValue === false){
            pollSyncStatus();
        }
    });

    $scope.$watch('dateRange', function (newValue, oldValue) {
        $scope.getTableData();
    });

    $scope.init();
}]);
