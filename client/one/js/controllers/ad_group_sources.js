/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupSourcesCtrl', ['$scope', '$state', '$location', '$window', '$timeout', 'api', 'zemCustomTableColsService', 'zemPostclickMetricsService', 'zemChartService', 'localStorageService', function ($scope, $state, $location, $window, $timeout, api, zemCustomTableColsService, zemPostclickMetricsService, zemChartService, localStorageService) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.isIncompletePostclickMetrics = false;
    $scope.selectedSourceIds = [];
    $scope.selectedTotals = true;
    $scope.constants = constants;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.chartMetricOptions = [];
    $scope.chartGoalMetrics = null;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-cost';
    $scope.sources = [];
    $scope.sourcesWaiting = null;

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

    $scope.updateSelectedRowsData = function () {
        if (!$scope.selectedTotals && !$scope.selectedSourceIds.length) {
            $scope.selectedTotals = true;
            $scope.totals.checked = true;
        }

        $location.search('source_ids', $scope.selectedSourceIds.join(','));
        $location.search('source_totals', $scope.selectedTotals ? 1 : null);

        $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);
        $scope.setAdGroupData('sourceTotals', $scope.selectedTotals);

        getDailyStats();
    };

    $scope.selectRows = function () {
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selectedSourceIds.indexOf(x.id) > -1;
        });
    };

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
               'bid_cpc', 'daily_budget', 'cost', 
               'cpc', 'clicks', 'impressions', 'ctr', 
               'yesterday_cost', 'supply_dash_url',
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

    $scope.postclickCategoryIndex = 1;

    $scope.columns = [
        {
            name: '',
            field: 'checked',
            type: 'checkbox',
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
            type: 'text',
            hasTotalsLabel: true,
            totalRow: false,
            help: 'A media source where your content is being promoted.',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'Status',
            field: 'status_label',
            unselectable: true,
            checked: true,
            type: 'text',
            totalRow: false,
            help: 'Status of a particular media source (enabled or paused).',
            extraThCss: 'text-center',
            extraTdCss: 'text-center',
            order: true,
            orderField: 'status',
            initialOrder: 'asc'
        },
        {
            name: 'Bid CPC',
            field: 'bid_cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.',
            totalRow: false,
            order: true,
            initialOrder: 'desc',
            onSave: function (sourceId, value, onError) {
                var data = {cpc_cc: value};

                api.adGroupSourceSettings.save($state.params.id, sourceId, data).then(
                    function (data) {
                        getTableData();
                    },
                    function (errors) {
                        onError(errors.cpc);
                    }
                );
            }
        },
        {
            name: 'Daily Budget',
            field: 'daily_budget',
            checked: true,
            type: 'currency',
            help: 'Maximum budget per day.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
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
            defaultValue: '0.0%',
            help: 'The number of clicks divided by the number of impressions.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Last OK Sync (EST)',
            field: 'last_sync',
            checked: false,
            type: 'datetime',
            help: 'Dashboard reporting data is synchronized on an hourly basis. This is when the most recent synchronization occurred (in Eastern Standard Time).',
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        }
    ];

    $scope.initColumns = function () {
        var cols;

        if ($scope.hasPermission('reports.yesterday_spend_view')) {
            $scope.columns.splice(5, 0, {
                name: 'Yesterday Spend',
                field: 'yesterday_cost',
                checked: false,
                type: 'currency',
                help: 'Amount that you have spent yesterday for promotion on specific media source.',
                internal: $scope.isPermissionInternal('reports.yesterday_spend_view'),
                totalRow: true,
                order: true,
                initialOrder: 'desc'
            });
        }

        if ($scope.hasPermission('zemauth.supply_dash_link_view')) {
            $scope.columns.splice(3, 0, {
                name: 'Link',
                field: 'supply_dash_url',
                checked: false,
                type: 'link',
                internal: $scope.isPermissionInternal('zemauth.supply_dash_link_view'),
                totalRow: true,
                order: true,
                initialOrder: 'desc'
            });
        }

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            zemPostclickMetricsService.insertColumns($scope.columns, $scope.isPermissionInternal('zemauth.postclick_metrics'));
        }

        cols = zemCustomTableColsService.load('adGroupSourcesCols', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('adGroupSourcesCols', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.$watch('isChartShown', function (newValue, oldValue) {
        zemChartService.save('zemChart', newValue);
    });

    $scope.loadRequestInProgress = false;

    $scope.orderTableData = function(order) {
        $scope.order = order;

        $location.search('order', $scope.order);
        localStorageService.set('adGroupSources.order', $scope.order);
        getTableData();
    };

    $scope.addGoalColumns = function(rows) {
        var alreadyAdded = function(field) {
            for(var i = 0; i < $scope.columns.length; i++) {
                if(field == $scope.columns[i]['field']){
                    return true;
                }
            }
            return false;
        };

        if($scope.hasPermission('zemauth.postclick_metrics')) {
            for(var i = 0; i < rows.length; i++) {
                for(var field in rows[i]) {
                    if(alreadyAdded(field)) {
                        continue;
                    }

                    if(field.indexOf(': Conversions') != -1) {
                        var col_descr = {
                            'name': field.substr('goal__'.length),
                            'field': field,
                            'checked': false,
                            'type': 'number',
                            'help': 'Number of completions of the conversion goal',
                            internal: $scope.isPermissionInternal('zemauth.postclick_metrics'),
                            totalRow: true,
                            order: true,
                            initialOrder: 'desc'
                        }
                        $scope.columns.splice($scope.columns.length - 1, 0, col_descr);
                        $scope.columnCategories[$scope.postclickCategoryIndex].fields.push(col_descr.field);
                    } else if(field.indexOf(': Conversion Rate') != -1) {
                        var col_descr = {
                            'name': field.substr('goal__'.length),
                            'field': field,
                            'checked': false,
                            'type': 'percent',
                            'help': 'Percentage of visits which resulted in a goal completion',
                            internal: $scope.isPermissionInternal('zemauth.postclick_metrics'),
                            totalRow: true,
                            order: true,
                            initialOrder: 'desc'
                        }
                        $scope.columns.splice($scope.columns.length - 1, 0, col_descr);
                        $scope.columnCategories[$scope.postclickCategoryIndex].fields.push(col_descr.field);
                    }
                }
            }
        }
    };

    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.adGroupSourcesTable.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.addGoalColumns(data.rows);

                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.totals.checked = $scope.selectedTotals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;

                $scope.selectRows();
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };

    var getDailyStatsMetrics = function () {
        var metrics = [$scope.chartMetric1, $scope.chartMetric2];

        var values = options.adGroupChartMetrics.map(function (option) {
            return option.value;
        });

        if (values.indexOf($scope.chartMetric1) === -1) {
            metrics.push(constants.chartMetric.CLICKS);
        }

        if (values.indexOf($scope.chartMetric2) === -1) {
            metrics.push(constants.chartMetric.IMPRESSIONS);
        }

        return metrics;
    };

    var setChartOptions = function (goals) {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions($scope.chartMetricOptions, $scope.isPermissionInternal('zemauth.postclick_metrics'));
        }

        if (goals) {
            $scope.chartMetricOptions = $scope.chartMetricOptions.concat(Object.keys(goals).map(function (goalId) {
                var typeName = {
                    'conversions': 'Conversions',
                    'conversion_rate': 'Conversion Rate'
                }[goals[goalId].type];

                if (typeName === undefined) {
                    return;
                }
                
                return {
                    name: goals[goalId].name + ': ' + typeName,
                    value: goalId,
                    internal: $scope.isPermissionInternal('zemauth.postclick_metrics')
                }
            }).filter(function (option) {
                return option !== undefined;
            }));
        }
    };

    var getDailyStats = function () {
        api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedSourceIds, $scope.selectedTotals, getDailyStatsMetrics()).then(
            function (data) {
                setChartOptions(data.goals);
            
                // Select default metrics if selected metrics are not defined
                var values = $scope.chartMetricOptions.map(function (option) {
                    return option.value;
                });

                if (values.indexOf($scope.chartMetric1) === -1) {
                    $scope.chartMetric1 = constants.chartMetric.CLICKS;
                }
                if (values.indexOf($scope.chartMetric2) === -1 && $scope.chartMetric2 !== 'none') {
                    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
                }

                $scope.chartData = data.chartData;
                $scope.chartGoalMetrics = data.goals;
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
        $scope.isChartShown = !$scope.isChartShown;
        $scope.chartBtnTitle = $scope.isChartShown ? 'Hide chart' : 'Show chart';
        $location.search('chart_hidden', !$scope.isChartShown ? '1' : null);

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
            $location.search('chart_metric1', $scope.chartMetric1);

            localStorageService.set('adGroupSources.chartMetric1', $scope.chartMetric1);
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
            $location.search('chart_metric2', $scope.chartMetric2);

            localStorageService.set('adGroupSources.chartMetric2', $scope.chartMetric2);
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

    $scope.init = function() {
        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get('adGroupSources.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get('adGroupSources.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;
        var order = $location.search().order || localStorageService.get('adGroupSources.order') || $scope.order;

        var data = $scope.adGroupData[$state.params.id];
        var sourceIds = $location.search().source_ids || (data && data.sourceIds && data.sourceIds.join(','));
        var sourceTotals = $location.search().source_totals || (data && data.sourceTotals ? 1 : null);

        setChartOptions();

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

        if (sourceIds) {
            $scope.selectedSourceIds = sourceIds.split(',');
            $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);
            $location.search('source_ids', sourceIds);

            if ($scope.rows) {
                $scope.selectRows();
            }
        }

        if (order !== undefined && $scope.order !== order) {
            $scope.order = order;
            $location.search('order', order);
        }

        $scope.selectedTotals = !$scope.selectedSourceIds.length || !!sourceTotals;
        $scope.setAdGroupData('sourceTotals', $scope.selectedTotals);
        $location.search('source_totals', sourceTotals);

        $scope.getAdGroupState();
        $scope.initColumns();

        getTableData();
        getDailyStats();

        getSources();
    };

    // export
    $scope.downloadReport = function() {
        $window.open('api/ad_groups/' + $state.params.id + '/sources/export/?type=' + $scope.exportType + '&start_date=' + $scope.dateRange.startDate.format() + '&end_date=' + $scope.dateRange.endDate.format(), '_blank');
        $scope.exportType = '';
    };

    var getSources = function () {
        if (!$scope.hasPermission('zemauth.ad_group_sources_add_source')) {
            return;
        }

        api.adGroupSources.get($state.params.id).then(
            function (data) {
                $scope.sources = data.sources;
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

                        if($scope.isSyncInProgress == false){
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
    }

    pollSyncStatus();

    // trigger sync
    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;
        api.adGroupSync.get($state.params.id);
    }

    $scope.init();
}]);
