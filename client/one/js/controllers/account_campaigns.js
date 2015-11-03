/*globals oneApp,constants,moment*/
oneApp.controller('AccountCampaignsCtrl', ['$window', '$location', '$scope', '$state', '$timeout', '$q', 'api', 'zemCustomTableColsService', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', function ($window, $location, $scope, $state, $timeout, $q, api, zemCustomTableColsService, zemPostclickMetricsService, zemFilterService, zemUserSettings) {
    $scope.getTableDataRequestInProgress = false;
    $scope.addCampaignRequestInProgress = false;
    $scope.isSyncInProgress = false;
    $scope.isSyncRecent = true;
    $scope.chartHidden = false;
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

    var userSettings = zemUserSettings.getInstance($scope, 'accountCampaigns'),
        canShowAddCampaignTutorial = $q.defer();

    $scope.showAddCampaignTutorial = function () {
        return canShowAddCampaignTutorial.promise;
    };

    $scope.exportOptions = [
        {name: 'By Day (CSV)', value: 'csv'},
        {name: 'By Day (Excel)', value: 'excel'}
    ];

    $scope.exportPlusOptions = [
      {name: 'Current View', value: 'view-csv'},
      {name: 'By Ad Group', value: 'adgroup-csv'},
      {name: 'By Content Ad', value: 'contentad-csv'}
    ];

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
            shown: true,
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
            shown: true,
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
            shown: true,
            totalRow: false,
            help: 'Status of a campaign (enabled or paused). A campaign is paused only if all its ad groups are paused too; otherwise, the campaign is enabled.',
            order: true,
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
            shown: true,
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
            shown: true,
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
            shown: true,
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
               'cost', 'cpc', 'clicks', 'impressions', 'ctr',
               'budget', 'available_budget', 'unspent_budget'
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
            function (campaignData) {
                $scope.accounts.forEach(function (account) {
                    if (account.id.toString() === accountId.toString()) {
                        account.campaigns.push({
                            id: campaignData.id,
                            name: campaignData.name,
                            adGroups: []
                        });

                        if ($window.isDemo) {
                            $state.go('main.campaigns.ad_groups', {id: campaignData.id});
                        } else {
                            $state.go('main.campaigns.settings', {id: campaignData.id});
                        }
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
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            getDailyStats();
        }
    });

    var getDailyStatsMetrics = function () {
        var values = $scope.chartMetricOptions.map(function (option) {
            return option.value;
        });

        if (values.indexOf($scope.chartMetric1) === -1) {
            $scope.chartMetric1 = constants.chartMetric.CLICKS;
        }

        if ($scope.chartMetric2 !== 'none' && values.indexOf($scope.chartMetric2) === -1) {
            $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
        }

        return [$scope.chartMetric1, $scope.chartMetric2];
    };

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.accountChartMetrics;

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
        api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedCampaignIds, $scope.selectedTotals, getDailyStatsMetrics(), null).then(
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
                $scope.dataStatus = data.dataStatus;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.order = data.order;

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;

                $scope.rows = $scope.rows.map(function (x) {
                    x.id = x.campaign;
                    x.name = {
                        text: x.name,
                        state: $scope.getDefaultCampaignState(),
                        id: x.campaign
                    };

                    if (x.archived) {
                        x.state = 'Archived';
                    } else if (x.state === constants.adGroupSettingsState.ACTIVE) {
                        x.state = 'Active';
                    } else {
                        x.state = 'Paused';
                    }

                    return x;
                });

                $scope.dataStatus = data.dataStatus;
                $scope.selectRows();

                canShowAddCampaignTutorial.resolve($scope.rows.length == 0);
                if ($scope.user.showOnboardingGuidance) {
                    $scope.user.automaticallyCreateAdGroup = $scope.rows.length == 0;
                }

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
        $scope.chartHidden = !$scope.chartHidden;
        $scope.chartBtnTitle = $scope.chartHidden ? 'Show chart' : 'Hide chart';

        $timeout(function() {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

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

        cols = zemCustomTableColsService.load('accountCampaigns', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('accountCampaigns', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.init = function() {
        var campaignIds = $location.search().campaign_ids;
        var campaignTotals = $location.search().campaign_totals;

        userSettings.register('chartMetric1');
        userSettings.register('chartMetric2');
        userSettings.register('order');
        userSettings.registerGlobal('chartHidden');

        setChartOptions();

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

        getTableData();
        initColumns();
        pollSyncStatus();
        getDailyStats();
        setDisabledExportOptions();
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('campaign_ids', null);
        $location.search('campaign_totals', null);
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

    var setDisabledExportOptions = function() {
      if($scope.hasPermission('zemauth.exports_plus')){
        api.exportPlusAllowed.get($state.params.id, 'accounts').then(
            function(data) {
                var option = null;
                $scope.exportPlusOptions.forEach(function(opt) {
                  if (opt.value === 'view-csv') {
                    opt.disabled = !data.view
                  }else if (opt.value === 'contentad-csv') {
                    opt.disabled = !data.content_ad
                  }else if (opt.value === 'adgroup-csv') {
                    opt.disabled = !data.ad_group
                  }
                });
            }
        );
      }
    };

    $scope.init();
}]);
