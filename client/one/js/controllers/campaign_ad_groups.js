/*globals oneApp,moment,constants,options*/
oneApp.controller('CampaignAdGroupsCtrl', ['$location', '$scope', '$state', '$timeout', 'api', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', function ($location, $scope, $state, $timeout, api, zemPostclickMetricsService, zemFilterService, zemUserSettings) {
    $scope.getTableDataRequestInProgress = false;
    $scope.addGroupRequestInProgress = false;
    $scope.isSyncInProgress = false;
    $scope.isSyncRecent = true;
    $scope.chartHidden = false;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = options.campaignChartMetrics;
    $scope.selectedAdGroupIds = [];
    $scope.selectedTotals = true;
    $scope.rows = null;
    $scope.totalRow = null;
    $scope.order = '-cost';
    $scope.isIncompletePostclickMetrics = false;
    $scope.localStoragePrefix = 'campaignAdGroups';

    var userSettings = zemUserSettings.getInstance($scope, 'campaignAdGroups');

    $scope.updateSelectedAdGroups = function (adGroupId) {
        adGroupId = adGroupId.toString();

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

        getDailyStats();
    };

    $scope.selectRows = function () {
        $scope.totalRow.checked = $scope.selectedTotals;
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selectedAdGroupIds.indexOf(x.ad_group.toString()) > -1;
        });
    };

    $scope.exportOptions = [
        {name: 'By Day (CSV)', value: 'csv'},
        {name: 'By Day (Excel)', value: 'excel'},
        {name: 'Detailed report', value: 'excel_detailed', hidden: !$scope.hasPermission('zemauth.campaign_ad_groups_detailed_report')}
    ];

    $scope.exportPlusOptions = [
      {name: 'Current View', value: 'adgroup-csv'},
      {name: 'By content Ad', value: 'contentad-csv'}
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
            name: 'Status',
            field: 'state',
            checked: true,
            type: 'text',
            shown: true,
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
            shown: true,
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
            shown: true,
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
               'cost', 'cpc', 'clicks', 'impressions', 'ctr'
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
            'fields': ['conversion_goal_1', 'conversion_goal_2']
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
        zemPostclickMetricsService.insertConversionGoalColumns(
            $scope.columns,
            $scope.columns.length - 2,
            $scope.hasPermission('zemauth.conversion_reports'),
            $scope.isPermissionInternal('zemauth.conversion_reports')
        );
    };

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
                                name: data.name,
                                contentAdsTabWithCMS: data.contentAdsTabWithCMS,
                                status: 'stopped',
                                state: 'paused'
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

        if ($scope.hasPermission('zemauth.conversion_reports')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                options.campaignConversionGoalChartMetrics,
                $scope.isPermissionInternal('zemauth.conversion_reports')
            );
        }
    };

    var getDailyStats = function () {
        api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedAdGroupIds, $scope.selectedTotals, getDailyStatsMetrics(), null).then(
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

    $scope.selectedAdGroupRemoved = function (id) {
        if (id !== 'totals') {
            $scope.updateSelectedAdGroups(id);
        } else {
            $scope.selectedTotals = false;
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
                $scope.totalRow.checked = $scope.selectedTotals;
                $scope.dataStatus = data.dataStatus;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.order = data.order;

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;
                zemPostclickMetricsService.setConversionGoalColumnsDefaults($scope.columns, data.conversionGoals, $scope.hasPermission('zemauth.conversion_reports'));

                $scope.rows = $scope.rows.map(function (x) {
                    x.id = x.ad_group;
                    x.name = {
                        text: x.name,
                        state: $scope.getDefaultAdGroupState(),
                        id: x.ad_group
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

        getTableData();
    };

    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;
        api.campaignSync.get($state.params.id, null);
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

    $scope.init = function() {
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

        $scope.selectedTotals = !$scope.selectedAdGroupIds.length || !!adGroupTotals;
        $location.search('ad_group_totals', adGroupTotals);

        getTableData();
        initColumns();
        pollSyncStatus();
        getDailyStats();
        setDisabledExportOptions();
    };

    $scope.$on('$stateChangeStart', function(event, toState, toParams, fromState, fromParams) {
        $location.search('ad_group_ids', null);
        $location.search('ad_group_totals', null);
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

        getDailyStats();
        getTableData();
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
        api.campaignAdGroupsExportAllowed.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate).then(
            function (data) {
                var option = null;
                $scope.exportOptions.forEach(function (opt) {
                    if (opt.value === 'excel_detailed') {
                        option = opt;
                    }
                });

                if (data.allowed) {
                    option.disabled = false;
                } else {
                    option.disabled = true;
                    option.maxDays = data.maxDays;
                }
            }
        );
    };

    $scope.init();
}]);
