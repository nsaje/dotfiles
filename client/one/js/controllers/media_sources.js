/*globals oneApp,moment,constants,options*/
oneApp.controller('MediaSourcesCtrl', ['$scope', '$state', 'zemUserSettings', '$location', 'api', 'zemPostclickMetricsService', 'zemFilterService', '$timeout', function ($scope, $state, zemUserSettings, $location, api, zemPostclickMetricsService, zemFilterService, $timeout) {
    $scope.localStoragePrefix = null;
    $scope.selectedTotals = true;
    $scope.selectedSourceIds = [];
    $scope.chartMetrics = [];
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartHidden = false;
    $scope.chartMetricOptions = [];
    $scope.chartBtnTitle = 'Hide chart';

    $scope.order = '-cost';
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.isIncompletePostclickMetrics = false;
    $scope.sources = [];
    $scope.exportOptions = [];
    $scope.infoboxHeader = null;
    $scope.infoboxSettings = null;
    $scope.infoboxLinkTo = null;

    var userSettings = null;

    $scope.updateSelectedSources = function (sourceId) {
        var i = $scope.selectedSourceIds.indexOf(sourceId);

        if (i > -1) {
            $scope.selectedSourceIds.splice(i, 1);
        } else {
            $scope.selectedSourceIds.push(sourceId);
        }

    };

    $scope.selectedSourcesChanged = function (row, checked) {
        if (row.id) {
            $scope.updateSelectedSources(row.id);
        } else {
            $scope.selectedTotals = !$scope.selectedTotals;
        }

        $scope.updateSelectedRowsData();
    };

    $scope.updateSelectedRowsLocation = function () {
        if (!$scope.selectedTotals && !$scope.selectedSourceIds.length) {
            $scope.selectedTotals = true;
            $scope.totals.checked = true;
        }
        if ($scope.selectedSourceIds.length > 0) {
            $location.search('source_ids', $scope.selectedSourceIds.join(','));
            $location.search('source_totals', $scope.selectedTotals ? 1 : null);
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
            x.checked = $scope.selectedSourceIds.indexOf(x.id) > -1;
        });
    };

    $scope.selectedSourceRemoved = function (sourceId) {
        if (sourceId !== 'totals') {
            $scope.updateSelectedSources(String(sourceId));
        } else {
            $scope.selectedTotals = false;
            $scope.totals.checked = false;
        }

        $scope.selectRows();
        $scope.updateSelectedRowsData();
    };

    $scope.removeFilteredSelectedSources = function () {
        if (zemFilterService.isSourceFilterOn()) {
            $scope.selectedSourceIds = $scope.selectedSourceIds.filter(function (sourceId) {
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
            hasPermission: $scope.hasPermission('zemauth.filter_sources'),
            clickCallback: zemFilterService.exclusivelyFilterSource,
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'A media source where your content is being promoted.',
            order: true,
            initialOrder: 'asc'
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
            field: 'yesterday_cost',
            checked: false,
            type: 'currency',
            help: 'Amount that you have spent yesterday for promotion on specific media source.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
            shown: !$scope.hasPermission('zemauth.can_view_effective_costs') && !$scope.hasPermission('zemauth.can_view_actual_costs')
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
            internal: $scope.isPermissionInternal('zemauth.can_view_effective_costs'),
            shown: $scope.hasPermission('zemauth.can_view_effective_costs')
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            help: 'Amount spent per media source.',
            totalRow: true,
            order: true,
            initialOrder: 'desc',
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
            help: 'The average CPC.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
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
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        }
    ];

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
                'min_bid_cpc', 'max_bid_cpc', 'daily_budget', 'cost', 'data_cost',
                'media_cost', 'e_media_cost', 'e_data_cost', 'total_cost', 'billing_cost',
                'cpc', 'clicks', 'impressions', 'ctr', 'license_fee',
                'yesterday_cost', 'e_yesterday_cost'
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
            'name': 'Conversions',
            'fields': ['conversion_goal_1', 'conversion_goal_2', 'conversion_goal_3', 'conversion_goal_4', 'conversion_goal_5']
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

        if ($scope.level === constants.level.CAMPAIGNS) {
            zemPostclickMetricsService.insertConversionGoalColumns(
                $scope.columns,
                $scope.columns.length - 2,
                $scope.hasPermission('zemauth.conversion_reports'),
                $scope.isPermissionInternal('zemauth.conversion_reports')
            );
        }
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!hasMetricData($scope.chartMetric1)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!hasMetricData($scope.chartMetric2)) {
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

        $timeout(function () {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    var hasMetricData = function (metric) {
        var hasData = false;
        $scope.chartData.forEach(function (group) {
            if (group.seriesData[metric] !== undefined) {
                hasData = true;
            }
        });

        return hasData;
    };

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
            conversionGoals,
            $scope.hasPermission('zemauth.conversion_reports')
        );
    };

    $scope.orderTableData = function (order) {
        $scope.order = order;
        getTableData();
    };


    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.sourcesTable.get($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.totals.checked = $scope.selectedTotals;
                $scope.dataStatus = data.dataStatus;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.selectRows();
                zemPostclickMetricsService.setConversionGoalColumnsDefaults($scope.columns, data.conversionGoals, $scope.hasPermission('zemauth.conversion_reports'));
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };

    var getDailyStats = function () {
        api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedSourceIds, $scope.selectedTotals, getDailyStatsMetrics(), true).then(
            function (data) {
                setConversionGoalChartOptions(data.conversionGoals);
                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    var getInfoboxData = function () {
        if (!$scope.hasPermission('zemauth.can_see_infobox')) {
            return;
        }

        if ($scope.level === constants.level.ALL_ACCOUNTS) {
            api.allAccountsOverview.get().then(
                function (data) {
                    $scope.infoboxHeader = data.header;
                    $scope.infoboxSettings = data.settings;
                }
            );
        } else if ($scope.level === constants.level.ACCOUNTS) {
            api.accountOverview.get($state.params.id).then(
                function (data) {
                    $scope.infoboxHeader = data.header;
                    $scope.infoboxSettings = data.settings;
                }
            );
        } else if ($scope.level === constants.level.CAMPAIGNS) {
            api.campaignOverview.get($state.params.id).then(
                function (data) {
                    $scope.infoboxHeader = data.header;
                    $scope.infoboxSettings = data.settings;
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

        if ($scope.level == constants.level.CAMPAIGNS && $scope.hasPermission('zemauth.conversion_reports')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                options.campaignConversionGoalChartMetrics,
                $scope.isPermissionInternal('zemauth.conversion_reports')
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

    var init = function () {

        if ($scope.level === constants.level.ALL_ACCOUNTS) {
            $scope.localStoragePrefix = 'allAccountSources';
            $scope.chartMetrics = options.allAccountsChartMetrics;
            $scope.chartMetric1 = constants.chartMetric.COST;
            $scope.chartMetric2 = constants.chartMetric.CLICKS;
            $scope.exportBaseUrl = 'api/' + constants.level.ALL_ACCOUNTS + '/sources/';
            $scope.exportPlusOptions = [
              {name: 'Current View', value: 'allaccounts-csv'},
              {name: 'By Account', value: 'account-csv'},
              {name: 'By Campaign', value: 'campaign-csv'},
              {name: 'By Ad Group', value: 'adgroup-csv'}
            ];

        } else if ($scope.level === constants.level.ACCOUNTS) {
            $scope.localStoragePrefix = 'accountSources';
            $scope.chartMetrics = options.accountChartMetrics;
            $scope.exportBaseUrl = 'api/' + constants.level.ACCOUNTS + '/' + $state.params.id + '/sources/';
            $scope.exportPlusOptions = [
              {name: 'Current View', value: 'account-csv'},
              {name: 'By Campaign', value: 'campaign-csv'},
              {name: 'By Ad Group', value: 'adgroup-csv'},
              {name: 'By Content Ad', value: 'contentad-csv'}
            ];
            $scope.infoboxLinkTo = 'main.accounts.settings';
        } else if ($scope.level === constants.level.CAMPAIGNS) {
            $scope.localStoragePrefix = 'campaignSources';
            $scope.chartMetrics = options.campaignChartMetrics;
            $scope.exportBaseUrl = 'api/' + constants.level.CAMPAIGNS + '/' + $state.params.id + '/sources/';
            $scope.exportPlusOptions = [
              {name: 'Current View', value: 'campaign-csv'},
              {name: 'By Ad Group', value: 'adgroup-csv'},
              {name: 'By Content Ad', value: 'contentad-csv'}
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
            $scope.selectedSourceIds = sourceIds.split(',');
            $scope.removeFilteredSelectedSources();
            $location.search('source_ids', sourceIds);
        }

        $scope.selectedTotals = !$scope.selectedSourceIds.length || !!sourceTotals;
        $location.search('source_totals', sourceTotals);

        $scope.initColumns();

        getDailyStats();
        getTableData();
        getInfoboxData();
        pollSyncStatus();
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

        getDailyStats();
        getTableData();
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
