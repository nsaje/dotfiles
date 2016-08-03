/*globals angular,oneApp,moment,constants,options*/

oneApp.controller('AdGroupSourcesCtrl', ['$scope', '$state', '$location', '$timeout', '$window', 'api', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', 'zemNavigationService', 'zemOptimisationMetricsService', function ($scope, $state, $location, $timeout, $window, api, zemPostclickMetricsService, zemFilterService, zemUserSettings, zemNavigationService, zemOptimisationMetricsService) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.isIncompletePostclickMetrics = false;
    $scope.constants = constants;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartHidden = false;
    $scope.chartMetricOptions = [];
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-media_cost';
    $scope.sources = [];
    $scope.sourcesWaiting = null;
    $scope.infoboxLinkTo = 'main.adGroups.settings';
    $scope.localStoragePrefix = 'adGroupSources';
    $scope.autopilotChanges = '';
    $scope.enablingAutopilotSourcesAllowed = true;
    $scope.loadRequestInProgress = false;

    $scope.selection = {
        entityIds: [],
        totals: true,
    };

    $scope.grid = {
        api: undefined,
        level: constants.level.AD_GROUPS,
        breakdown: constants.breakdown.MEDIA_SOURCE,
        entityId: $state.params.id,
    };

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    $scope.exportOptions = [
      {name: 'Current View', value: constants.exportType.AD_GROUP},
      {name: 'By Content Ad', value: constants.exportType.CONTENT_AD},
    ];

    $scope.updateSelectedSources = function (sourceId) {
        var i = $scope.selection.entityIds.indexOf(sourceId);

        if (i > -1) {
            $scope.selection.entityIds.splice(i, 1);
        } else {
            $scope.selection.entityIds.push(sourceId);
        }

        $scope.columns[0].disabled = $scope.selection.entityIds.length >= constants.maxSelectedSources;
    };

    $scope.selectedSourcesChanged = function (row, checked) {
        if (row.id) {
            $scope.updateSelectedSources(row.id);
        } else {
            $scope.selection.totals = !$scope.selection.totals;
        }

        $scope.updateSelectedRowsData();
    };

    $scope.updateSelectedRowsLocation = function () {
        if (!$scope.selection.totals && !$scope.selection.entityIds.length) {
            $scope.selection.totals = true;
            $scope.totals.checked = true;
        }

        if ($scope.selection.entityIds.length > 0) {
            $location.search('source_ids', $scope.selection.entityIds.join(','));
            $location.search('source_totals', $scope.selection.totals ? 1 : null);
        } else {
            $location.search('source_ids', null);
            $location.search('source_totals', null);
        }

        $scope.setAdGroupData('sourceIds', $scope.selection.entityIds);
        $scope.setAdGroupData('sourceTotals', $scope.selection.totals);
    };

    $scope.updateSelectedRowsData = function () {
        $scope.updateSelectedRowsLocation();
        $scope.getDailyStats();
    };

    $scope.selectRows = function () {
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selection.entityIds.indexOf(x.id) > -1;
        });
    };

    $scope.removeFilteredSelectedSources = function () {
        if (zemFilterService.isSourceFilterOn()) {
            $scope.selection.entityIds = $scope.selection.entityIds.filter(function (sourceId) {
                return zemFilterService.isSourceFiltered(sourceId);
            });
        }
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
            selectCallback: $scope.selectedSourcesChanged,
            disabled: false
        },
        {
            name: '\u25CF',
            field: 'status_setting',
            type: 'state',
            order: true,
            initialOrder: 'asc',
            enabledValue: constants.adGroupSourceSettingsState.ACTIVE,
            pausedValue: constants.adGroupSourceSettingsState.INACTIVE,
            internal: false,
            shown: true,
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'A setting for enabling and pausing media sources.',
            onChange: function (sourceId, value) {
                var newSettings = {};
                if (value) {
                    newSettings.state = value;
                }
                $scope.loadRequestInProgress = true;
                $scope.autopilotChanges = '';

                zemNavigationService.notifyAdGroupReloading($state.params.id, true);
                api.adGroupSourceSettings.save(
                    $state.params.id,
                    sourceId,
                    newSettings
                ).then(
                    function (data) {
                        $scope.rows.forEach(function (row) {
                            if (row.id === sourceId) {
                                row.editable_fields = data.editable_fields;
                            }
                        });
                        $scope.autopilotChanges = data.autopilot_changed_sources;
                        $scope.enablingAutopilotSourcesAllowed = data.enabling_autopilot_sources_allowed;
                        $scope.pollSourcesTableUpdates();

                        // reload ad group to update its status
                        zemNavigationService.reloadAdGroup($state.params.id);
                        $scope.loadRequestInProgress = false;
                    }
                );
            },
            getDisabledMessage: function (row) {
                var editableFields = row.editable_fields;
                if (!editableFields) {
                    return '';
                }

                return editableFields['status_setting'].message;
            },
            enablingAutopilotSourcesNotAllowed: function () {
                return !$scope.enablingAutopilotSourcesAllowed;
            },
            disabled: false
        },
        {
            name: 'Media Source',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'clickPermissionOrText',
            hasPermission: $scope.hasPermission('zemauth.can_filter_sources_through_table'),
            clickCallback: zemFilterService.exclusivelyFilterSource,
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'A media source where your content is being promoted.',
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
            field: 'status',
            unselectable: true,
            checked: true,
            type: 'notification',
            extraTdCss: 'notification',
            shown: true,
            totalRow: false,
            help: 'Status of a particular media source (enabled or paused).',
            order: true,
            orderField: 'status',
            initialOrder: 'asc'
        },
        {
            name: 'Link',
            field: 'supply_dash_url',
            checked: false,
            type: 'link',
            internal: $scope.isPermissionInternal('zemauth.supply_dash_link_view'),
            shown: $scope.hasPermission('zemauth.supply_dash_link_view'),
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Bid CPC',
            field: 'bid_cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            settingsField: true,
            initialOrder: 'desc',
            statusSettingEnabledValue: constants.adGroupSourceSettingsState.ACTIVE,
            onSave: function (sourceId, value, onSuccess, onError) {
                var data = {cpc_cc: value};

                api.adGroupSourceSettings.save($state.params.id, sourceId, data).then(
                    function (data) {
                        onSuccess();
                        $scope.pollSourcesTableUpdates();
                    },
                    function (errors) {
                        onError(errors.cpc);
                    }
                );
            },
            adGroupAutopilotOn: function () {
                return $scope.adGroupAutopilotState !== constants.adGroupSettingsAutopilotState.INACTIVE;
            },
        },
        {
            name: 'Current Bid CPC',
            field: 'current_bid_cpc',
            fractionSize: 3,
            checked: false,
            type: 'currency',
            internal: false,
            shown: false,
            totalRow: false,
            order: true,
            help: 'Cost-per-click (CPC) bid is the approximate amount that you\'ll be charged for a click on your ad.',
            initialOrder: 'desc'
        },
        {
            name: 'Daily Budget',
            field: 'daily_budget',
            fractionSize: 0,
            checked: true,
            type: 'currency',
            shown: true,
            help: 'Maximum budget per day.',
            totalRow: true,
            order: true,
            settingsField: true,
            initialOrder: 'desc',
            statusSettingEnabledValue: constants.adGroupSourceSettingsState.ACTIVE,
            onSave: function (sourceId, value, onSuccess, onError) {
                var data = {daily_budget_cc: value};

                api.adGroupSourceSettings.save($state.params.id, sourceId, data).then(
                    function (data) {
                        onSuccess();
                        $scope.pollSourcesTableUpdates();
                    },
                    function (errors) {
                        onError(errors.dailyBudget);
                    }
                );
            },
            adGroupAutopilotOn: function () {
                return $scope.adGroupAutopilotState === constants.adGroupSettingsAutopilotState.ACTIVE_CPC_BUDGET;
            },
        },
        {
            name: 'Current Daily Budget',
            field: 'current_daily_budget',
            checked: false,
            fractionSize: 0,
            type: 'currency',
            internal: false,
            shown: false,
            totalRow: true,
            order: true,
            help: 'Maximum budget per day.',
            initialOrder: 'desc'
        },
        {
            name: 'Actual Yesterday Spend',
            field: 'yesterday_cost',
            checked: false,
            type: 'currency',
            help: 'Amount that you have spent yesterday for promotion on specific media source, including overspend.',
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
            help: 'Amount that you have spent yesterday for promotion on specific media source.',
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
            help: 'The number of times a content ad has been displayed.',
            totalRow: true,
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
            help: 'The number of clicks divided by the number of impressions.',
            totalRow: true,
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
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        }
    ];

    $scope.columnCategories = [
        {
            'name': 'Costs',
            'fields': [
                'data_cost', 'yesterday_cost', 'e_yesterday_cost',
                'media_cost', 'e_media_cost', 'e_data_cost', 'billing_cost',
                'license_fee', 'margin', 'agency_total',
            ],
        },
        {
            'name': 'Traffic Acquisition',
            'fields': [
                'bid_cpc', 'daily_budget',
                'cpc', 'cpm', 'clicks', 'impressions', 'ctr',
                'supply_dash_url',
                'current_bid_cpc', 'current_daily_budget',
            ]
        },
        {
            'name': 'Audience Metrics',
            'fields': [
                'visits', 'pageviews', 'percent_new_users',
                'bounce_rate', 'pv_per_visit', 'avg_tos',
                'click_discrepancy', 'unique_users', 'returning_users',
                'bounced_visits',
            ]
        },
        {
            'name': 'Conversions',
            'fields': ['conversion_goal_1', 'conversion_goal_2', 'conversion_goal_3', 'conversion_goal_4', 'conversion_goal_5']
        },
        zemOptimisationMetricsService.createColumnCategories(),
        {
            'name': 'Data Sync',
            'fields': ['last_sync']
        }
    ];

    $scope.initColumns = function () {
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

        zemPostclickMetricsService.insertConversionGoalColumns(
            $scope.columns,
            $scope.columns.length - 2,
            true,
            false
        );

        zemOptimisationMetricsService.insertAudienceOptimizationColumns(
            $scope.columns,
            $scope.columns.length - 2,
            $scope.hasPermission('zemauth.campaign_goal_optimization'),
            $scope.isPermissionInternal('zemauth.campaign_goal_optimization')
        );
    };

    $scope.orderTableData = function (order) {
        $scope.order = order;
        getTableData();
    };

    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.adGroupSourcesTable.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                var defaultChartMetrics;
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.totals.checked = $scope.selection.totals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;
                $scope.notifications = data.notifications;
                $scope.lastChange = data.lastChange;
                $scope.dataStatus = data.dataStatus;
                $scope.adGroupAutopilotState = data.adGroupAutopilotState;
                $scope.enablingAutopilotSourcesAllowed = data.enabling_autopilot_sources_allowed;
                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;
                $scope.campaignGoals = data.campaign_goals;
                $scope.selectRows();
                $scope.pollSourcesTableUpdates();
                zemPostclickMetricsService.setConversionGoalColumnsDefaults($scope.columns, data.conversionGoals);
                zemOptimisationMetricsService.updateVisibility($scope.columns, $scope.campaignGoals);
                zemOptimisationMetricsService.updateChartOptionsVisibility($scope.chartMetricOptions, $scope.campaignGoals);
                // when switching windows between campaigns with campaign goals defined and campaigns without campaign goals defined
                // make sure chart selection gets updated
                defaultChartMetrics = $scope.defaultChartMetrics($scope.chartMetric1, $scope.chartMetric2, $scope.chartMetricOptions);
                $scope.chartMetric1 = defaultChartMetrics.metric1 || $scope.chartMetric1;
                $scope.chartMetric2 = defaultChartMetrics.metric2 || $scope.chartMetric2;
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
    if ($window.isDemo) {
        $window.demoActions.refreshAdGroupSourcesTable = getTableData;
    }

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

    var setConversionGoalChartOptions = function (conversionGoals) {
        var validChartMetrics = zemPostclickMetricsService.getValidChartMetrics($scope.chartMetric1, $scope.chartMetric2, conversionGoals);
        $scope.chartMetric1 = validChartMetrics.chartMetric1;
        $scope.chartMetric2 = validChartMetrics.chartMetric2;
        zemPostclickMetricsService.setConversionGoalChartOptions(
            $scope.chartMetricOptions,
            conversionGoals
        );
    };

    var setChartOptions = function () {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

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

        $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
            $scope.chartMetricOptions,
            options.adGroupConversionGoalChartMetrics,
            false,
            true
        );

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

        if ($scope.hasPermission('zemauth.campaign_goal_optimization')) {
            $scope.chartMetricOptions = zemOptimisationMetricsService.concatChartOptions(
                $scope.campaignGoals,
                $scope.chartMetricOptions,
                options.campaignGoalChartMetrics.concat(options.campaignGoalConversionGoalChartMetrics),
                $scope.isPermissionInternal('zemauth.campaign_goal_optimization')
            );
        }
    };

    $scope.getDailyStats = function () {
        api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selection.entityIds, $scope.selection.totals, getDailyStatsMetrics(), null).then(
            function (data) {
                setConversionGoalChartOptions(data.conversionGoals);
                $scope.conversionGoals = data.conversionGoals;
                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    var getInfoboxData = function () {
        api.adGroupOverview.get(
            $state.params.id,
            $scope.dateRange.startDate,
            $scope.dateRange.endDate).then(
            function (data) {
                $scope.setInfoboxHeader(data.header);
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
            }
        );
    };

    $scope.selectedSourceRemoved = function (sourceId) {
        if (sourceId !== 'totals') {
            $scope.updateSelectedSources(String(sourceId));
        } else {
            $scope.selection.totals = false;
            $scope.totals.checked = false;
        }

        $scope.selectRows();
        $scope.updateSelectedRowsData();
    };

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;
        $scope.chartBtnTitle = $scope.chartHidden ? 'Show chart' : 'Hide chart';

        $timeout(function () {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    var hasMetricData = function (metric) {
        var hasData = false;
        $scope.chartData && $scope.chartData.groups.forEach(function (group) {
            if (group.seriesData[metric] !== undefined) {
                hasData = true;
            }
        });

        return hasData;
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!hasMetricData($scope.chartMetric1)) {
                $scope.getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!hasMetricData($scope.chartMetric2)) {
                $scope.getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    $scope.$watch('isSyncInProgress', function (newValue, oldValue) {
        if (newValue === true && oldValue === false) {
            pollSyncStatus();
        }
    });

    // From parent scope (mainCtrl).
    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
            return;
        }

        $scope.getDailyStats();
        getTableData();
    });

    $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        $scope.removeFilteredSelectedSources();
        $scope.updateSelectedRowsLocation();

        getTableData();
        $scope.getDailyStats();
    }, true);

    $scope.init = function () {
        var data = $scope.adGroupData[$state.params.id];
        var sourceIds = $location.search().source_ids || (data && data.sourceIds && data.sourceIds.join(','));
        var sourceTotals = $location.search().source_totals || (data && data.sourceTotals ? 1 : null);

        setChartOptions();

        userSettings.registerWithoutWatch('chartMetric1');
        userSettings.registerWithoutWatch('chartMetric2');
        userSettings.register('order');
        userSettings.registerGlobal('chartHidden');

        if (sourceIds) {
            $scope.selection.entityIds = sourceIds.split(',');
            $scope.removeFilteredSelectedSources();
            $scope.setAdGroupData('sourceIds', $scope.selection.entityIds);
            $location.search('source_ids', sourceIds);

            if ($scope.rows) {
                $scope.selectRows();
            }
        }

        $scope.selection.totals = !$scope.selection.entityIds.length || !!sourceTotals;
        $scope.setAdGroupData('sourceTotals', $scope.selection.totals);
        $location.search('source_totals', sourceTotals);

        $scope.initColumns();

        getTableData();
        $scope.getDailyStats();
        getInfoboxData();

        getSources();
    };

    var getSources = function () {
        if (!$scope.hasPermission('zemauth.ad_group_sources_add_source')) {
            return;
        }

        api.adGroupSources.get($state.params.id).then(
            function (data) {
                var sources = [];
                for (var source, i = 0; i < data.sources.length; i++) {
                    source = data.sources[i];

                    var notificationMsg = '';
                    if (!source.canTargetExistingRegions) {
                        notificationMsg = source.name + ' doesn\'t support DMA targeting. Turn off DMA targeting to add ' + source.name + '.';
                    }
                    if (!source.canRetarget) {
                        notificationMsg = (notificationMsg ? notificationMsg + ' ' : '') + source.name + ' doesn\'t support retargeting. Turn off retargeting to add ' + source.name + '.';
                    }
                    sources.push({
                        name: source.name,
                        value: source.id,
                        hasPermission: true,
                        disabled: !source.canTargetExistingRegions || !source.canRetarget,
                        notification: notificationMsg,
                    });
                }

                $scope.sources = sources;
                $scope.sourcesWaiting = data.sourcesWaiting;
                if ($scope.sourcesWaiting && $scope.sourcesWaiting.length > 0) {
                    // Create grid notification (and close old one if exists)
                    var msg = 'We are adding the following media source(s): ' +
                        $scope.sourcesWaiting.join(', ') + '. This may take some time.';
                    if ($scope.grid.sourcesWaitingNotification) {
                        $scope.grid.api.closeNotification ($scope.grid.sourcesWaitingNotification);
                    }
                    $scope.grid.sourcesWaitingNotification = $scope.grid.api.notify (constants.notificationType.info, msg, false);
                }
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.addSource = function (sourceIdToAdd) {
        if (!sourceIdToAdd) {
            return;
        }

        api.adGroupSources.add($state.params.id, sourceIdToAdd).then(
            function (data) {
                getSources();
            },
            function (data) {
                // error
                return;
            }
        );

        $scope.sourceIdToAdd = '';
    };

    var pollSyncStatus = function () {
        if ($scope.isSyncInProgress) {
            $timeout(function () {
                api.checkSyncProgress.get($state.params.id).then(
                    function (data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if ($scope.isSyncInProgress === false) {
                            // we found out that the sync is no longer in progress
                            // time to reload the data
                            getTableData();
                            $scope.getDailyStats();
                        }
                    },
                    function (data) {
                        // error
                        $scope.isSyncInProgress = false;
                    }
                ).finally(function () {
                    pollSyncStatus();
                });
            }, 10000);
        }
    };

    pollSyncStatus();

    $scope.pollSourcesTableUpdates = function () {
        if ($scope.lastChangeTimeout) {
            return;
        }

        api.adGroupSourcesUpdates.get($state.params.id, $scope.lastChange)
            .then(function (data) {
                if (data.lastChange) {
                    $scope.lastChange = data.lastChange;
                    $scope.notifications = data.notifications;
                    $scope.dataStatus = data.dataStatus;

                    updateTableData(data.rows, data.totals);
                }

                if (data.inProgress) {
                    $scope.lastChangeTimeout = $timeout(function () {
                        $scope.lastChangeTimeout = null;
                        $scope.pollSourcesTableUpdates();
                    }, 5000);
                }
            });
    };

    var updateTableData = function (rowsUpdates, totalsUpdates) {
        $scope.rows.forEach(function (row) {
            var rowUpdates = rowsUpdates[row.id];
            if (rowUpdates) {
                updateObject(row, rowUpdates);
            }
        });

        updateObject($scope.totals, totalsUpdates);
    };

    var updateObject = function (object, updates) {
        for (var key in updates) {
            if (updates.hasOwnProperty(key)) {
                object[key] = updates[key];
            }
        }
    };

    $scope.$on('$destroy', function () {
        $timeout.cancel($scope.lastChangeTimeout);
    });

    // trigger sync
    $scope.triggerSync = function () {
        $scope.isSyncInProgress = true;
        api.adGroupSync.get($state.params.id);
    };

    zemNavigationService.onUpdate($scope, function () {
        $scope.updateInfoboxHeader($scope);
    });

    $scope.init();
}]);
