/* globals moment,constants,options,angular */
angular.module('one.legacy').controller('CampaignAdGroupsCtrl', ['$location', '$scope', '$state', '$timeout', 'api', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', 'zemNavigationService', 'zemDataSourceService', 'zemGridEndpointService', function ($location, $scope, $state, $timeout, api, zemPostclickMetricsService, zemFilterService, zemUserSettings, zemNavigationService, zemDataSourceService, zemGridEndpointService) { // eslint-disable-line max-len
    $scope.getTableDataRequestInProgress = false;
    $scope.addGroupRequestInProgress = false;
    $scope.isSyncInProgress = false;
    $scope.isSyncRecent = true;
    $scope.chartHidden = false;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = options.campaignChartMetrics;
    $scope.rows = null;
    $scope.totalRow = null;
    $scope.order = '-media_cost';
    $scope.isIncompletePostclickMetrics = false;
    $scope.localStoragePrefix = 'campaignAdGroups';
    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.infoboxLinkTo = 'main.campaigns.settings';

    $scope.selection = {
        entityIds: [],
        totals: true,
    };

    $scope.grid = {
        api: undefined,
        level: constants.level.CAMPAIGNS,
        breakdown: constants.breakdown.AD_GROUP,
        entityId: $state.params.id,
    };

    var userSettings = zemUserSettings.getInstance($scope, 'campaignAdGroups');

    $scope.updateSelectedAdGroups = function (adGroupId) {
        adGroupId = adGroupId.toString();

        var i = $scope.selection.entityIds.indexOf(adGroupId);
        if (i > -1) {
            $scope.selection.entityIds.splice(i, 1);
        } else {
            $scope.selection.entityIds.push(adGroupId);
        }

        $scope.columns[0].disabled = $scope.selection.entityIds.length >= 4;
    };

    $scope.selectedAdGroupsChanged = function (row, checked) {
        if (row.ad_group) {
            $scope.updateSelectedAdGroups(row.ad_group);
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

        $location.search('ad_group_ids', $scope.selection.entityIds.join(','));
        $location.search('ad_group_totals', $scope.selection.totals ? 1 : null);

        getDailyStats();
    };

    $scope.selectRows = function () {
        $scope.totalRow.checked = $scope.selection.totals;
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selection.entityIds.indexOf(x.ad_group.toString()) > -1;
        });
    };

    $scope.exportOptions = [
        {name: 'By Campaign (totals)', value: constants.exportType.CAMPAIGN},
        {name: 'Current View', value: constants.exportType.AD_GROUP, defaultOption: true},
        {name: 'By Content Ad', value: constants.exportType.CONTENT_AD},
    ];

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
            selectCallback: $scope.selectedAdGroupsChanged,
            disabled: false
        },
        {
            name: '\u25CF',
            field: 'state',
            type: 'state',
            order: true,
            editable: true,
            initialOrder: 'asc',
            enabledValue: constants.adGroupSourceSettingsState.ACTIVE,
            pausedValue: constants.adGroupSourceSettingsState.INACTIVE,
            internal: $scope.isPermissionInternal('zemauth.can_control_ad_group_state_in_table'),
            shown: $scope.hasPermission('zemauth.can_control_ad_group_state_in_table'),
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'A setting for enabling and pausing Ad Groups.',
            onChange: function (adgroupId, state) {
                $scope.rows.forEach(function (row) {
                    if (row.id === adgroupId) {
                        row.stateText = $scope.getStateText(state);
                    }
                });
                zemNavigationService.notifyAdGroupReloading(adgroupId, true);

                api.adGroupSettingsState.post(adgroupId, state).then(
                    function (data) {
                        // reload ad group to update its status
                        zemNavigationService.reloadAdGroup(adgroupId);
                    },
                    function () {
                        zemNavigationService.notifyAdGroupReloading(adgroupId, false);
                    }
                );
            },
            getDisabledMessage: function (row) {
                return row.editable_fields.state.message;
            },
            disabled: false,
            archivedField: 'archived'
        },
        {
            name: 'Ad Group',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'linkNav',
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'Name of the ad group.',
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
            field: 'stateText',
            unselectable: true,
            checked: true,
            type: 'text',
            shown: true,
            totalRow: false,
            help: 'Status of an ad group (enabled or paused).',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'Actual Yesterday Spend',
            field: 'yesterday_cost',
            checked: false,
            type: 'currency',
            help: 'Amount that you have spent yesterday for promotion on specific ad group, including overspend.',
            totalRow: true,
            order: true,
            internal: $scope.isPermissionInternal('zemauth.can_view_actual_costs'),
            initialOrder: 'desc',
            shown: $scope.hasPermission('zemauth.can_view_actual_costs')
        },
        {
            name: 'Yesterday Spend',
            field: 'e_yesterday_cost',
            checked: false,
            type: 'currency',
            help: 'Amount that you have spent yesterday for promotion on specific ad group.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_platform_cost_breakdown'),
            shown: $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
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
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            totalRow: true,
            help: 'The average CPC for each ad group.',
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
            help: 'The number of times ad group\'s content ads have been clicked.',
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
            help: 'The number of times ad group\'s content ads have been displayed.',
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
                'license_fee', 'yesterday_cost', 'e_yesterday_cost',
                'margin', 'agency_total',
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
                'click_discrepancy', 'unique_users', 'new_users', 'returning_users',
                'bounced_visits', 'non_bounced_visits', 'total_seconds',
            ]
        },
        {
            'name': 'Conversions',
            'fields': ['conversion_goals_placeholder', 'pixels_placeholder']
        },
        {
            'name': 'Goals',
            'fields': ['avg_cost_per_visit', 'avg_cost_for_new_visitor', 'avg_cost_per_pageview',
                       'avg_cost_per_non_bounced_visit', 'avg_cost_per_minute', 'conversion_goals_avg_cost_placeholder',
                       'pixels_avg_cost_placeholder'],
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

    $scope.addAdGroup = function () {
        var campaignId = $state.params.id;
        $scope.addGroupRequestInProgress = true;

        api.campaignAdGroups.create(campaignId).then(
            function (data) {
                zemNavigationService.addAdGroupToCache(campaignId, {
                    id: data.id,
                    name: data.name,
                    status: constants.adGroupSettingsState.INACTIVE,
                    state: constants.adGroupRunningStatus.INACTIVE,
                });
                $state.go('main.adGroups.settings', {id: data.id});
            },
            function () {
                // error
                return;
            }
        ).finally(function () {
            $scope.addGroupRequestInProgress = false;
        });
    };

    $scope.getInfoboxData = function () {
        api.campaignOverview.get(
            $state.params.id,
            $scope.dateRange.startDate,
            $scope.dateRange.endDate
        ).then(
            function (data) {
                $scope.infoboxHeader = data.header;
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
            }
        );
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

    var refreshChartOptions = function (conversionGoals, pixels) {
        zemPostclickMetricsService.insertConversionsGoalChartOptions($scope.chartMetricOptions, conversionGoals);
        zemPostclickMetricsService.insertPixelChartOptions($scope.chartMetricOptions, pixels);

        var validChartMetrics = zemPostclickMetricsService.getValidChartMetrics($scope.chartMetric1, $scope.chartMetric2, $scope.chartMetricOptions);
        if ($scope.chartMetric1 !== validChartMetrics.metric1) $scope.chartMetric1 = validChartMetrics.metric1;
        if ($scope.chartMetric2 !== validChartMetrics.metric2) $scope.chartMetric2 = validChartMetrics.metric2;
    };

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.campaignChartMetrics;

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
        api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selection.entityIds, $scope.selection.totals, getDailyStatsMetrics(), null).then(
            function (data) {
                refreshChartOptions(data.conversionGoals, data.pixels);
                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.selectedAdGroupRemoved = function (id) {
        if (id !== 'totals') {
            $scope.updateSelectedAdGroups(id);
        } else {
            $scope.selection.totals = false;
        }

        $scope.selectRows();
        $scope.updateSelectedRowsData();
    };

    var getTableData = function () {
        $scope.getTableDataRequestInProgress = true;

        api.campaignAdGroupsTable.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totalRow = data.totals;
                $scope.totalRow.checked = $scope.selection.totals;
                $scope.dataStatus = data.dataStatus;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;
                $scope.campaignGoals = data.campaign_goals;

                $scope.order = data.order;

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;
                zemPostclickMetricsService.insertConversionGoalColumns($scope.columns, $scope.columnCategories, data.conversionGoals);
                zemPostclickMetricsService.insertPixelColumns($scope.columns, $scope.columnCategories, data.pixels);

                $scope.rows = $scope.rows.map(function (x) {
                    x.id = x.ad_group;
                    x.name = {
                        text: x.name,
                        state: $scope.getDefaultAdGroupState(),
                        id: x.ad_group
                    };

                    if (x.archived) {
                        x.stateText = 'Archived';
                    } else {
                        x.stateText = $scope.getStateText(x.state);
                    }

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
            $scope.reflowGraph(1);
        });
    };

    $scope.getStateText = function (state) {
        if (state === constants.adGroupSettingsState.ACTIVE) {
            return 'Active';
        }

        return 'Paused';
    };

    $scope.orderTableData = function (order) {
        $scope.order = order;

        getTableData();
    };

    $scope.triggerSync = function () {
        $scope.isSyncInProgress = true;
        api.campaignSync.get($state.params.id, null);
    };

    var pollSyncStatus = function () {
        if ($scope.isSyncInProgress) {
            $timeout(function () {
                api.checkCampaignSyncProgress.get($state.params.id).then(
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
        var adGroupIds = $location.search().ad_group_ids;
        var adGroupTotals = $location.search().ad_group_totals;

        setChartOptions();

        userSettings.registerWithoutWatch('chartMetric1');
        userSettings.registerWithoutWatch('chartMetric2');
        userSettings.register('order');
        userSettings.registerGlobal('chartHidden');

        if (adGroupIds) {
            adGroupIds.split(',').forEach(function (id) {
                $scope.updateSelectedAdGroups(id);
            });
            $location.search('ad_group_ids', adGroupIds);
        }

        $scope.selection.totals = !$scope.selection.entityIds.length || !!adGroupTotals;
        $location.search('ad_group_totals', adGroupTotals);

        getTableData();
        initColumns();
        pollSyncStatus();
        getDailyStats();
        $scope.getContentInsights();
        $scope.getInfoboxData();

        $scope.setActiveTab();
    };

    $scope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
        $location.search('ad_group_ids', null);
        $location.search('ad_group_totals', null);
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

        if (newValue.startDate.isValid() && newValue.endDate.isValid()) {
            getDailyStats();
            getTableData();

            $scope.getContentInsights();
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
