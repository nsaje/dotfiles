/*globals oneApp,constants,moment*/
oneApp.controller('AccountCampaignsCtrl', ['$window', '$location', '$scope', '$state', '$timeout', '$q', 'api', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', 'zemNavigationService', function ($window, $location, $scope, $state, $timeout, $q, api, zemPostclickMetricsService, zemFilterService, zemUserSettings, zemNavigationService) { // eslint-disable-line max-len
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
    $scope.localStoragePrefix = 'accountCampaigns';
    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.infoboxLinkTo = 'main.accounts.settings';

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix),
        canShowAddCampaignTutorial = $q.defer();

    $scope.showAddCampaignTutorial = function () {
        return canShowAddCampaignTutorial.promise;
    };

    $scope.exportOptions = [
        {name: 'By Day (CSV)', value: 'csv'},
        {name: 'By Day (Excel)', value: 'excel'}
    ];

    $scope.exportPlusOptions = [
      {name: 'Current View', value: 'campaign-csv'},
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
            nameCssClass: 'performance-icon',
            field: 'performance',
            unselectable: true,
            checked: true,
            type: 'icon',
            totalRow: false,
            help: 'Goal performance indicator',
            order: true,
            initialOrder: 'asc',
            internal: $scope.isPermissionInternal('zemauth.campaign_goal_performance'),
            shown: $scope.hasPermission('zemauth.campaign_goal_performance')
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
            name: 'Campaign Manager',
            field: 'campaign_manager',
            checked: false,
            type: 'text',
            totalRow: false,
            help: 'Campaign manager responsible for the campaign and the communication with the client.',
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_see_managers_in_campaigns_table'),
            shown: $scope.hasPermission('zemauth.can_see_managers_in_campaigns_table'),
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
            totalRow: true,
            help: 'The amount spent per campaign.',
            order: true,
            initialOrder: 'desc',
            isDefaultOrder: true,
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
                'cost', 'data_cost', 'cpc', 'clicks', 'impressions', 'ctr',
                'budget', 'available_budget', 'unspent_budget',
                'media_cost', 'e_media_cost', 'e_data_cost', 'total_cost', 'billing_cost',
                'license_fee'
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
            'name': 'Management',
            'fields': [
                'campaign_manager'
            ]
        },
        {
            'name': 'Data Sync',
            'fields': ['last_sync']
        }
    ];

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

    $scope.addCampaign = function () {
        var accountId = $state.params.id;
        $scope.addCampaignRequestInProgress = true;

        api.accountCampaigns.create(accountId).then(
            function (campaignData) {
                zemNavigationService.addCampaignToCache(accountId, {
                    id: campaignData.id,
                    name: campaignData.name,
                    adGroups: [],
                });
                if ($window.isDemo) {
                    $state.go('main.campaigns.ad_groups', {id: campaignData.id});
                } else {
                    $state.go('main.campaigns.settings', {id: campaignData.id});
                }
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

        // always query for default metrics
        var metrics = [constants.chartMetric.CLICKS, constants.chartMetric.IMPRESSIONS];
        if (values.indexOf($scope.chartMetric1) === -1) {
            $scope.chartMetric1 = constants.chartMetric.CLICKS;
        } else {
            metrics.push($scope.chartMetric1);
        }

        if ($scope.chartMetric2 !== 'none' && values.indexOf($scope.chartMetric2) === -1) {
            $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
        } else {
            metrics.push($scope.chartMetric2);
        }

        return metrics;
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

    $scope.getInfoboxData = function () {
        if (!$scope.hasInfoboxPermission()) {
            return;
        }

        api.accountOverview.get($state.params.id).then(
            function (data) {
                $scope.infoboxHeader = data.header;
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
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
            $scope.reflowGraph(1);
        });
    };

    $scope.orderTableData = function (order) {
        $scope.order = order;

        getTableData();
    };

    $scope.triggerSync = function () {
        $scope.isSyncInProgress = true;
        api.campaignSync.get(null, $state.params.id);
    };

    var pollSyncStatus = function () {
        if ($scope.isSyncInProgress) {
            $timeout(function () {
                api.checkCampaignSyncProgress.get(null, $state.params.id).then(
                    function (data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if (!$scope.isSyncInProgress) {
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

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;
        $scope.chartBtnTitle = $scope.chartHidden ? 'Show chart' : 'Hide chart';

        $timeout(function () {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    $scope.init = function () {
        var campaignIds = $location.search().campaign_ids;
        var campaignTotals = $location.search().campaign_totals;

        userSettings.registerWithoutWatch('chartMetric1');
        userSettings.registerWithoutWatch('chartMetric2');
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
        $scope.getInfoboxData();
    };

    $scope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
        $location.search('campaign_ids', null);
        $location.search('campaign_totals', null);
    });

    $scope.$watch('isSyncInProgress', function (newValue, oldValue) {
        if (newValue === true && oldValue === false) {
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

    $scope.init();
}]);
