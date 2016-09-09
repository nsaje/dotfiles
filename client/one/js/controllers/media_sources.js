/* globals moment,constants,options,angular */
angular.module('one.legacy').controller('MediaSourcesCtrl', ['$scope', '$state', 'zemUserSettings', '$location', 'api', 'zemPostclickMetricsService', 'zemFilterService', '$timeout', function ($scope, $state, zemUserSettings, $location, api, zemPostclickMetricsService, zemFilterService, $timeout) { // eslint-disable-line max-len
    $scope.localStoragePrefix = null;
    $scope.chartMetrics = [];
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartHidden = false;
    $scope.chartMetricOptions = [];
    $scope.chartBtnTitle = 'Hide chart';

    $scope.order = '-media_cost';
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.isIncompletePostclickMetrics = false;
    $scope.sources = [];
    $scope.exportOptions = [];
    $scope.infoboxHeader = null;
    $scope.infoboxBasicSettings = null;
    $scope.infoboxPerformanceSettings = null;
    $scope.infoboxLinkTo = null;
    $scope.sideBarVisible = false;

    $scope.selection = {
        entityIds: [],
        totals: true,
    };

    $scope.grid = {
        api: undefined,
        level: $scope.level,
        breakdown: constants.breakdown.MEDIA_SOURCE,
        entityId: $state.params.id,
    };

    var userSettings = null,
        hasCampaignGoals = $scope.level === constants.level.CAMPAIGNS;

    $scope.updateSelectedSources = function (sourceId) {
        var i = $scope.selection.entityIds.indexOf(sourceId);

        if (i > -1) {
            $scope.selection.entityIds.splice(i, 1);
        } else {
            $scope.selection.entityIds.push(sourceId);
        }

        $scope.columns[0].disabled = $scope.selection.entityIds.length >= constants.maxSelectedSources;
    };

    $scope.selectedSourcesChanged = function (row) {
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
    };

    $scope.updateSelectedRowsData = function () {
        $scope.updateSelectedRowsLocation();
        getDailyStats();
    };

    $scope.selectRows = function () {
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selection.entityIds.indexOf(x.id) > -1;
        });
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
            shown: $scope.hasPermission('zemauth.campaign_goal_performance') && hasCampaignGoals
        },
        {
            name: 'Status',
            field: 'status',
            unselectable: true,
            checked: true,
            type: 'text',
            shown: true,
            totalRow: false,
            help: 'Status of a particular media source (enabled or paused).',
            order: true,
            orderField: 'status',
            initialOrder: 'asc'
        },
        {
            name: 'Min Bid',
            field: 'min_bid_cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'Minimum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Max Bid',
            field: 'max_bid_cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Daily Budget',
            field: 'daily_budget',
            checked: true,
            type: 'currency',
            shown: true,
            help: 'Maximum budget per day.',
            totalRow: true,
            order: true,
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
            initialOrder: 'desc',
            internal: $scope.isPermissionInternal('zemauth.can_view_actual_costs'),
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
                'data_cost', 'media_cost', 'e_media_cost', 'e_data_cost',
                'license_fee', 'billing_cost',
                'margin', 'agency_total',
                'yesterday_cost', 'e_yesterday_cost',
            ]
        },
        {
            'name': 'Traffic Acquisition',
            'fields': [
                'min_bid_cpc', 'max_bid_cpc', 'daily_budget',
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

    $scope.initColumns = function () {
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

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;
        $scope.chartBtnTitle = $scope.chartHidden ? 'Show chart' : 'Hide chart';

        $scope.reflowGraph(0);
    };

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

    $scope.orderTableData = function (order) {
        $scope.order = order;
        getTableData();
    };


    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.sourcesTable.get($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                var defaultChartMetrics;
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.totals.checked = $scope.selection.totals;
                $scope.dataStatus = data.dataStatus;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.selectRows();
                if ($scope.level === constants.level.CAMPAIGNS) {
                    $scope.campaignGoals = data.campaign_goals;
                    zemPostclickMetricsService.insertConversionGoalColumns($scope.columns, $scope.columnCategories, data.conversionGoals);
                    zemPostclickMetricsService.insertPixelColumns($scope.columns, $scope.columnCategories, data.pixels);
                } else if ($scope.level === constants.level.ACCOUNTS) {
                    zemPostclickMetricsService.insertPixelColumns($scope.columns, $scope.columnCategories, data.pixels);
                }
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

    var getDailyStats = function () {
        if ($scope.dailyStatsPromise !== undefined) {
            $scope.dailyStatsPromise.abort();
        }

        $scope.dailyStatsPromise = api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate,
            $scope.dateRange.endDate, $scope.selection.entityIds, $scope.selection.totals, getDailyStatsMetrics(), true);

        $scope.dailyStatsPromise.then(
            function (data) {
                refreshChartOptions(data.conversionGoals, data.pixels);
                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.dailyStatsPromise = undefined;
        });
    };

    var updateInfoboxData = function (data) {
        $scope.infoboxHeader = data.header;
        $scope.infoboxBasicSettings = data.basicSettings;
        $scope.infoboxPerformanceSettings = data.performanceSettings;
        $scope.reflowGraph(1);
    };

    $scope.getInfoboxData = function () {
        if ($scope.level === constants.level.ALL_ACCOUNTS) {
            api.allAccountsOverview.get($scope.dateRange.startDate, $scope.dateRange.endDate).then(
                function (data) {
                    updateInfoboxData(data);
                }
            );
        } else if ($scope.level === constants.level.ACCOUNTS) {
            api.accountOverview.get($state.params.id).then(
                function (data) {
                    updateInfoboxData(data);
                }
            );
        } else if ($scope.level === constants.level.CAMPAIGNS) {
            api.campaignOverview.get(
                $state.params.id,
                $scope.dateRange.startDate,
                $scope.dateRange.endDate
            ).then(
                function (data) {
                    updateInfoboxData(data);
                }
            );
        }
    };

    var setChartOptions = function () {
        $scope.chartMetricOptions = $scope.chartMetrics;

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

    var init = function () {
        if ($scope.level === constants.level.ALL_ACCOUNTS) {
            $scope.localStoragePrefix = 'allAccountSources';
            $scope.chartMetrics = options.allAccountsChartMetrics;
            $scope.chartMetric1 = constants.chartMetric.COST;
            $scope.chartMetric2 = constants.chartMetric.CLICKS;
            $scope.exportBaseUrl = 'api/' + constants.level.ALL_ACCOUNTS + '/sources/';
            $scope.exportOptions = [
              {name: 'Current View', value: constants.exportType.ALL_ACCOUNTS},
              {name: 'By Account', value: constants.exportType.ACCOUNT},
              {name: 'By Campaign', value: constants.exportType.CAMPAIGN},
              {name: 'By Ad Group', value: constants.exportType.AD_GROUP},
            ];

        } else if ($scope.level === constants.level.ACCOUNTS) {
            $scope.localStoragePrefix = 'accountSources';
            $scope.chartMetrics = options.accountChartMetrics;
            $scope.exportBaseUrl = 'api/' + constants.level.ACCOUNTS + '/' + $state.params.id + '/sources/';
            $scope.exportOptions = [
              {name: 'Current View', value: constants.exportType.ACCOUNT},
              {name: 'By Campaign', value: constants.exportType.CAMPAIGN},
              {name: 'By Ad Group', value: constants.exportType.AD_GROUP},
              {name: 'By Content Ad', value: constants.exportType.CONTENT_AD},
            ];
            $scope.infoboxLinkTo = 'main.accounts.settings';
        } else if ($scope.level === constants.level.CAMPAIGNS) {
            $scope.localStoragePrefix = 'campaignSources';
            $scope.chartMetrics = options.campaignChartMetrics;
            $scope.exportBaseUrl = 'api/' + constants.level.CAMPAIGNS + '/' + $state.params.id + '/sources/';
            $scope.exportOptions = [
              {name: 'Current View', value: constants.exportType.CAMPAIGN},
              {name: 'By Ad Group', value: constants.exportType.AD_GROUP},
              {name: 'By Content Ad', value: constants.exportType.CONTENT_AD},
            ];

            $scope.infoboxLinkTo = 'main.campaigns.settings';
        }

        userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

        var sourceIds = $location.search().source_ids;
        var sourceTotals = $location.search().source_totals;

        setChartOptions();

        userSettings.registerWithoutWatch('chartMetric1');
        userSettings.registerWithoutWatch('chartMetric2');
        userSettings.register('order');
        userSettings.registerGlobal('chartHidden');

        if (sourceIds) {
            $scope.selection.entityIds = sourceIds.split(',');
            $scope.removeFilteredSelectedSources();
            $location.search('source_ids', sourceIds);
        }

        $scope.selection.totals = !$scope.selection.entityIds.length || !!sourceTotals;
        $location.search('source_totals', sourceTotals);

        $scope.initColumns();

        getDailyStats();
        getTableData();
        $scope.getInfoboxData();
        pollSyncStatus();

        if ($scope.hasPermission('zemauth.can_view_sidetabs') && $scope.level === constants.level.CAMPAIGNS) {
            $scope.sideBarVisible = true;
            $scope.getContentInsights();
        } else {
            $scope.sideBarVisible = false;
        }

        $scope.setActiveTab();
    };

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

        if (newValue.startDate.isValid() && newValue.endDate.isValid()) {
            // on all accounts some settings depend on date range
            if ($scope.level === constants.level.ALL_ACCOUNTS) {
                $scope.getInfoboxData();
            }
            getDailyStats();
            getTableData();

            if ($scope.hasPermission('zemauth.can_view_sidetabs') && $scope.level === constants.level.CAMPAIGNS) {
                $scope.sideBarVisible = true;
                $scope.getContentInsights();
            }
        }
    });

    $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        $scope.removeFilteredSelectedSources();
        $scope.updateSelectedRowsLocation();

        getTableData();
        getDailyStats();
    }, true);

    $scope.$on('$stateChangeStart', function (event, toState, toParams, fromState, fromParams) {
        $location.search('source_ids', null);
        $location.search('source_totals', null);
    });

    var pollSyncStatus = function () {
        if ($scope.isSyncInProgress) {
            $timeout(function () {
                var promise = null;

                if ($scope.level === constants.level.ALL_ACCOUNTS) {
                    promise = api.checkAccountsSyncProgress.get();
                } else if ($scope.level === constants.level.ACCOUNTS) {
                    promise = api.checkCampaignSyncProgress.get(undefined, $state.params.id);
                } else if ($scope.level === constants.level.CAMPAIGNS) {
                    promise = api.checkCampaignSyncProgress.get($state.params.id, null);
                }

                promise.then(
                    function (data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if ($scope.isSyncInProgress === false) {
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

    $scope.triggerSync = function () {
        $scope.isSyncInProgress = true;

        if ($scope.level === constants.level.ALL_ACCOUNTS) {
            api.accountSync.get();
        } else if ($scope.level === constants.level.ACCOUNTS) {
            api.campaignSync.get(null, $state.params.id);
        } else if ($scope.level === constants.level.CAMPAIGNS) {
            api.campaignSync.get($state.params.id, null);
        }
    };

    init();
}]);
