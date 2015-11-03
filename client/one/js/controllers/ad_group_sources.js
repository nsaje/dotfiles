/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupSourcesCtrl', ['$scope', '$state', '$location', '$timeout', '$window', 'api', 'zemCustomTableColsService', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', function ($scope, $state, $location, $timeout, $window, api, zemCustomTableColsService, zemPostclickMetricsService, zemFilterService, zemUserSettings) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.isIncompletePostclickMetrics = false;
    $scope.selectedSourceIds = [];
    $scope.selectedTotals = true;
    $scope.constants = constants;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartHidden = false;
    $scope.chartMetricOptions = [];
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-cost';
    $scope.sources = [];
    $scope.sourcesWaiting = null;

    var userSettings = zemUserSettings.getInstance($scope, 'adGroupSources');

    $scope.exportOptions = [
      {name: 'By Day (CSV)', value: 'csv'},
      {name: 'By Day (Excel)', value: 'excel'}
    ];

    $scope.exportPlusOptions = [
      {name: 'Current View', value: 'view-csv'},
      {name: 'By Content Ad', value: 'contentad-csv'}
    ];

    $scope.updateSelectedSources = function (sourceId) {
        var i = $scope.selectedSourceIds.indexOf(sourceId);

        if (i > -1) {
            $scope.selectedSourceIds.splice(i, 1);
        } else {
            $scope.selectedSourceIds.push(sourceId);
        }

        $scope.columns[0].disabled = $scope.selectedSourceIds.length >= 4;
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

        $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);
        $scope.setAdGroupData('sourceTotals', $scope.selectedTotals);
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

    $scope.removeFilteredSelectedSources = function () {
        if (zemFilterService.isSourceFilterOn()) {
            $scope.selectedSourceIds = $scope.selectedSourceIds.filter(function (sourceId) {
                return zemFilterService.isSourceFiltered(sourceId);
            });
        }
    };

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
               'bid_cpc', 'daily_budget', 'cost',
               'cpc', 'clicks', 'impressions', 'ctr',
               'yesterday_cost', 'supply_dash_url',
               'current_bid_cpc', 'current_daily_budget'
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
            'fields': []
        },
        {
            'name': 'Data Sync',
            'fields': ['last_sync']
        }
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
            selectCallback: $scope.selectedSourcesChanged,
            disabled: false
        },
        {
            name: '',
            nameCssClass: 'active-circle-icon-gray',
            field: 'status_setting',
            type: 'state',
            enabledValue: constants.adGroupSourceSettingsState.ACTIVE,
            pausedValue: constants.adGroupSourceSettingsState.INACTIVE,
            autopilotEnabledValue: constants.adGroupSourceSettingsAutopilotState.ACTIVE,
            autopilotPausedValue: constants.adGroupSourceSettingsAutopilotState.INACTIVE,
            autopilotInternal: $scope.isPermissionInternal('zemauth.can_set_media_source_to_auto_pilot'),
            autopilotShown: $scope.hasPermission('zemauth.can_set_media_source_to_auto_pilot'),
            internal: $scope.isPermissionInternal('zemauth.set_ad_group_source_settings'),
            shown: $scope.hasPermission('zemauth.set_ad_group_source_settings'),
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'A setting for enabling and pausing media sources.',
            onChange: function (sourceId, value) {
                api.adGroupSourceSettings.save($state.params.id, sourceId, {state: value}).then(
                    function (data) {
                        $scope.pollSourcesTableUpdates();
                    }
                );
            },
            onAutopilotChange: function (sourceId, value) {
              api.adGroupSourceSettings.save($state.params.id, sourceId, {autopilot_state: value}).then(
                  function (data) {

                    $scope.rows.forEach(function (row) {
                        if (row.id === sourceId) {
                            row.editable_fields = data.editable_fields
                        }
                    });

                      $scope.pollSourcesTableUpdates();
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
            settingsField: $scope.hasPermission('zemauth.set_ad_group_source_settings'),
            initialOrder: 'desc',
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
            }
        },
        {
            name: 'Current Bid CPC',
            field: 'current_bid_cpc',
            fractionSize: 3,
            checked: false,
            type: 'currency',
            internal: $scope.isPermissionInternal('zemauth.see_current_ad_group_source_state'),
            shown: $scope.hasPermission('zemauth.see_current_ad_group_source_state'),
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
            settingsField: $scope.hasPermission('zemauth.set_ad_group_source_settings'),
            initialOrder: 'desc',
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
            }
        },
        {
            name: 'Current Daily Budget',
            field: 'current_daily_budget',
            checked: false,
            fractionSize: 0,
            type: 'currency',
            internal: $scope.isPermissionInternal('zemauth.see_current_ad_group_source_state'),
            shown: $scope.hasPermission('zemauth.see_current_ad_group_source_state'),
            totalRow: true,
            order: true,
            help: 'Maximum budget per day.',
            initialOrder: 'desc'
        },
        {
            name: 'Yesterday Spend',
            field: 'yesterday_cost',
            checked: false,
            type: 'currency',
            help: 'Amount that you have spent yesterday for promotion on specific media source.',
            shown: 'true',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            shown: true,
            help: "Amount spent per media source.",
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: "The average CPC.",
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

        var cols = zemCustomTableColsService.load('adGroupSources', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('adGroupSources', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.loadRequestInProgress = false;

    $scope.orderTableData = function(order) {
        $scope.order = order;
        getTableData();
    };

    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.adGroupSourcesTable.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                zemPostclickMetricsService.insertConversionGoalColumns(
                    $scope.columns,
                    $scope.columns.length - 2,
                    data.conversionGoals,
                    $scope.columnCategories[2],
                    $scope.hasPermission('zemauth.conversion_reports'),
                    $scope.isPermissionInternal('zemauth.conversion_reports')
                );

                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.totals.checked = $scope.selectedTotals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;
                $scope.notifications = data.notifications;
                $scope.lastChange = data.lastChange;
                $scope.dataStatus = data.dataStatus;

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;

                $scope.selectRows();
                $scope.pollSourcesTableUpdates();
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };
    if ($window.isDemo) {
        $window.demoActions.refreshAdGroupSourcesTable = getTableData;
    }

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

    var setChartOptions = function (conversionGoals) {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

        if ($scope.hasPermission('zemauth.aggregate_postclick_acquisition')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatAcquisitionChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.aggregate_postclick_acquisition')
            );
        }

        if (conversionGoals) {
            $scope.chartMetricOptions = $scope.chartMetricOptions.concat(conversionGoals.map(function (goal) {
                return {
                    name: goal['name'],
                    value: 'conversion_goal_' + goal['id'],
                    internal: $scope.isPermissionInternal('zemauth.conversion_reports')
                };
            }));
        }
    };

    var getDailyStats = function () {
        api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedSourceIds, $scope.selectedTotals, getDailyStatsMetrics(), null).then(
            function (data) {
                setChartOptions(data.conversionGoals);

                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        );
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

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;
        $scope.chartBtnTitle = $scope.chartHidden ? 'Show chart' : 'Hide chart';

        $timeout(function() {
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

    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if(newValue === true && oldValue === false){
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

    $scope.init = function() {
        var data = $scope.adGroupData[$state.params.id];
        var sourceIds = $location.search().source_ids || (data && data.sourceIds && data.sourceIds.join(','));
        var sourceTotals = $location.search().source_totals || (data && data.sourceTotals ? 1 : null);

        userSettings.register('chartMetric1');
        userSettings.register('chartMetric2');
        userSettings.register('order');
        userSettings.registerGlobal('chartHidden');

        setChartOptions(null);

        if (sourceIds) {
            $scope.selectedSourceIds = sourceIds.split(',');
            $scope.removeFilteredSelectedSources();
            $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);
            $location.search('source_ids', sourceIds);

            if ($scope.rows) {
                $scope.selectRows();
            }
        }

        $scope.selectedTotals = !$scope.selectedSourceIds.length || !!sourceTotals;
        $scope.setAdGroupData('sourceTotals', $scope.selectedTotals);
        $location.search('source_totals', sourceTotals);

        $scope.getAdGroupState();
        $scope.initColumns();

        getTableData();
        getDailyStats();

        getSources();
        setDisabledExportOptions();
    };

    var getSources = function () {
        if (!$scope.hasPermission('zemauth.ad_group_sources_add_source')) {
            return;
        }

        api.adGroupSources.get($state.params.id).then(
            function (data) {
                var sources = [];
                for (var source, i=0; i<data.sources.length; i++) {
                    source = data.sources[i];
                    sources.push({
                        name: source.name,
                        value: source.id,
                        hasPermission: true,
                        disabled: !source.canTargetExistingRegions,
                        notification: (!source.canTargetExistingRegions ? source.name + " doesn't support DMA targeting. Turn off DMA targeting to add " + source.name + '.' : undefined)
                    });
                }

                $scope.sources = sources;
                $scope.sourcesWaiting = data.sourcesWaiting;
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

    var pollSyncStatus = function() {
        if($scope.isSyncInProgress){
            $timeout(function() {
                api.checkSyncProgress.get($state.params.id).then(
                    function(data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if($scope.isSyncInProgress === false){
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
            }, 10000);
        }
    };

    pollSyncStatus();

    $scope.pollSourcesTableUpdates = function () {
        if (!$scope.hasPermission('zemauth.set_ad_group_source_settings') ||
            $scope.lastChangeTimeout) {
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
    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;
        api.adGroupSync.get($state.params.id);
    };

    var setDisabledExportOptions = function() {
      if($scope.hasPermission('zemauth.exports_plus')){
        api.sourcesExportPlusAllowed.get($state.params.id, 'ad_groups').then(
            function(data) {
                var option = null;
                $scope.exportPlusOptions.forEach(function(opt) {
                  if (opt.value === 'view-csv') {
                    opt.disabled = !data.view
                  }else if (opt.value === 'contentad-csv') {
                    opt.disabled = !data.content_ad
                  }
                });
            }
        );
      }
    };

    $scope.init();
}]);
