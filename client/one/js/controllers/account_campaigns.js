/*globals angular,constants,options,moment*/
angular.module('one.legacy').controller('AccountCampaignsCtrl', ['$window', '$location', '$scope', '$state', '$timeout', '$q', 'api', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', 'zemNavigationService', 'zemDataFilterService', function ($window, $location, $scope, $state, $timeout, $q, api, zemPostclickMetricsService, zemFilterService, zemUserSettings, zemNavigationService, zemDataFilterService) { // eslint-disable-line max-len
    $scope.getTableDataRequestInProgress = false;
    $scope.addCampaignRequestInProgress = false;
    $scope.isSyncInProgress = false;
    $scope.isSyncRecent = true;
    $scope.chartHidden = false;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = options.accountChartMetrics;
    $scope.selectedTotals = true;
    $scope.rows = null;
    $scope.totalRow = null;
    $scope.order = '-media_cost';
    $scope.isIncompletePostclickMetrics = false;
    $scope.localStoragePrefix = 'accountCampaigns';
    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.infoboxLinkTo = 'main.accounts.settings';

    $scope.selection = {
        entityIds: [],
        totals: true,
    };

    $scope.grid = {
        api: undefined,
        level: constants.level.ACCOUNTS,
        breakdown: constants.breakdown.CAMPAIGN,
        entityId: $state.params.id,
    };

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    $scope.exportOptions = [
      {name: 'By Account (totals)', value: constants.exportType.ACCOUNT},
      {name: 'Current View', value: constants.exportType.CAMPAIGN, defaultOption: true},
      {name: 'By Ad Group', value: constants.exportType.AD_GROUP},
      {name: 'By Content Ad', value: constants.exportType.CONTENT_AD},
    ];

    $scope.updateSelectedCampaigns = function (campaignId) {
        campaignId = campaignId.toString();

        var i = $scope.selection.entityIds.indexOf(campaignId);
        if (i > -1) {
            $scope.selection.entityIds.splice(i, 1);
        } else {
            $scope.selection.entityIds.push(campaignId);
        }

        $scope.columns[0].disabled = $scope.selection.entityIds.length >= 4;
    };

    $scope.selectedCampaignsChanged = function (row, checked) {
        if (row.campaign) {
            $scope.updateSelectedCampaigns(row.campaign);
        } else {
            $scope.selection.totals = !$scope.selection.totals;
        }

        $scope.updateSelectedRowsData();
    };

    $scope.updateSelectedRowsData = function () {
        if (!$scope.selection.totals && !$scope.selection.entityIds.length) {
            $scope.selection.totals = true;
            $scope.totalRow.checked = true;
        }

        $location.search('campaign_ids', $scope.selection.entityIds.join(','));
        $location.search('campaign_totals', $scope.selection.totals ? 1 : null);

        getDailyStats();
    };

    $scope.selectRows = function () {
        $scope.totalRow.checked = $scope.selection.totals;
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selection.entityIds.indexOf(x.campaign.toString()) > -1;
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
            type: 'icon-list',
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
            name: 'Avg. CPM',
            field: 'cpm',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            help: 'Cost per 1,000 impressions',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
            shown: true,
            internal: false,
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
            'fields': [
                'data_cost', 'media_cost', 'e_media_cost', 'e_data_cost', 'billing_cost',
                'license_fee', 'margin', 'agency_total',
            ],
        },
        {
            'name': 'Projections',
            fields: [
                'spend_projection', 'pacing', 'allocated_budgets', 'license_fee_projection',
            ],
        },
        {
            'name': 'Traffic Acquisition',
            'fields': [
                'cpc', 'clicks', 'impressions', 'ctr', 'cpm',
            ]
        },
        {
            'name': 'Audience Metrics',
            'fields': [
                'visits', 'pageviews', 'percent_new_users',
                'bounce_rate', 'pv_per_visit', 'avg_tos',
                'click_discrepancy', 'unique_users', 'new_users', 'returning_users', 'bounced_visits',
                'non_bounced_visits', 'total_seconds',
            ]
        },
        {
            'name': 'Management',
            'fields': [
                'campaign_manager'
            ]
        },
        {
            name: 'Conversions',
            fields: ['conversion_goals_placeholder', 'pixels_placeholder']
        },
        {
            'name': 'Goals',
            'fields': ['avg_cost_per_visit', 'avg_cost_for_new_visitor', 'avg_cost_per_pageview',
                       'avg_cost_per_non_bounced_visit', 'avg_cost_per_minute', 'pixels_avg_cost_placeholder'],
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

        zemPostclickMetricsService.insertConversionsPlaceholders(
            $scope.columns,
            $scope.columns.length - 2
        );

        zemPostclickMetricsService.insertAudienceOptimizationColumns(
            $scope.columns,
            $scope.columns.length - 2
        );

        zemPostclickMetricsService.insertCPAPlaceholders(
            $scope.columns,
            $scope.columns.length - 2
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
            if (!$scope.isMetricInChartData(newValue, $scope.chartData)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!$scope.isMetricInChartData(newValue, $scope.chartData)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    var getDailyStatsMetrics = function () {
        // always query for default metrics
        var metrics = [$scope.chartMetric1, $scope.chartMetric2];
        if (metrics.indexOf(constants.chartMetric.CLICKS) < 0) {
            metrics.push(constants.chartMetric.CLICKS);
        }
        if (metrics.indexOf(constants.chartMetric.IMPRESSIONS) < 0) {
            metrics.push(constants.chartMetric.IMPRESSIONS);
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
            options.conversionChartMetrics
        );

        $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
            $scope.chartMetricOptions,
            options.goalChartMetrics
        );
    };

    var getDailyStats = function () {
        var dateRange = zemDataFilterService.getDateRange();
        api.dailyStats.list($scope.level, $state.params.id, dateRange.startDate, dateRange.endDate, $scope.selection.entityIds, $scope.selection.totals, getDailyStatsMetrics(), null).then(
            function (data) {
                refreshChartOptions(data.pixels);
                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    var refreshChartOptions = function (pixels) {
        zemPostclickMetricsService.insertPixelChartOptions($scope.chartMetricOptions, pixels);

        var validChartMetrics = zemPostclickMetricsService.getValidChartMetrics($scope.chartMetric1, $scope.chartMetric2, $scope.chartMetricOptions);
        if ($scope.chartMetric1 !== validChartMetrics.metric1) {
            $scope.chartMetric1 = validChartMetrics.metric1;
        }

        if ($scope.chartMetric2 !== validChartMetrics.metric2) {
            $scope.chartMetric2 = validChartMetrics.metric2;
        }
    };

    $scope.getInfoboxData = function () {
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
            $scope.selection.totals = false;
        }

        $scope.selectRows();
        $scope.updateSelectedRowsData();
    };

    var getTableData = function () {
        $scope.getTableDataRequestInProgress = true;

        var dateRange = zemDataFilterService.getDateRange();
        api.accountCampaignsTable.get($state.params.id, dateRange.startDate, dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totalRow = data.totals;
                $scope.totalRow.checked = $scope.selection.totals;
                $scope.dataStatus = data.dataStatus;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.order = data.order;

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;
                zemPostclickMetricsService.insertPixelColumns($scope.columns, $scope.columnCategories, data.pixels);

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

        $scope.selection.totals = !$scope.selection.entityIds.length || !!campaignTotals;
        $location.search('campaign_totals', campaignTotals);

        getTableData();
        initColumns();
        pollSyncStatus();
        getDailyStats();
        $scope.getInfoboxData();

        $scope.setActiveTab();

        zemDataFilterService.onDateRangeUpdate(function () {
            getTableData();
            getDailyStats();
        });
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
