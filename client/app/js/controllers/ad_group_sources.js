/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupSourcesCtrl', ['$scope', '$state', '$location', '$window', '$timeout', 'api', 'zemCustomTableColsService', 'zemChartService', 'localStorageService', function ($scope, $state, $location, $window, $timeout, api, zemCustomTableColsService, zemChartService, localStorageService) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.isIncompletePostclickMetrics = false;
    $scope.selectedSourceIds = [];
    $scope.selectedSourceTotals = true;
    $scope.constants = constants;
    $scope.chartMetric1 = constants.sourceChartMetric.CLICKS;
    $scope.chartMetric2 = constants.sourceChartMetric.IMPRESSIONS;
    $scope.dailyStats = [];
    $scope.chartData = undefined;
    $scope.isChartShown = zemChartService.load('zemChart');
    $scope.sourceChartMetrics = options.sourceChartMetrics;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-cost';
    $scope.sources = [];
    $scope.sourcesWaiting = null;
    $scope.columns = [
        {
            name: 'Bid CPC',
            field: 'bid_cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            help: 'Maximum bid price (in USD) per click.'
        },
        {
            name: 'Daily Budget',
            field: 'daily_budget',
            checked: true,
            type: 'currency',
            help: 'Maximum budget per day.'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            help: "Amount spent per media source."
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            help: "The average CPC."
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
            help: 'The number of times a content ad has been clicked.'
        },
        {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number',
            help: 'The number of times a content ad has been displayed.'
        },
        {
            name: 'CTR',
            field: 'ctr',
            checked: true,
            type: 'percent',
            help: 'The number of clicks divided by the number of impressions.'
        },
        {
            name: 'Last OK Sync',
            field: 'last_sync',
            checked: false,
            type: 'datetime',
            help: 'Dashboard reporting data is synchronized on an hourly basis. This is when the most recent synchronization occurred.'
        }
    ];

    $scope.initColumns = function () {
        var cols;

        if ($scope.hasPermission('reports.yesterday_spend_view')) {
            $scope.columns.splice(2, 0, {
                name: 'Yesterday Spend',
                field: 'yesterday_cost',
                checked: false,
                type: 'currency',
                help: 'Amount that you have spent yesterday for promotion on specific media source.',
                internal: $scope.isPermissionInternal('reports.yesterday_spend_view')
            });
        }

        if ($scope.hasPermission('zemauth.supply_dash_link_view')) {
            $scope.columns.splice(0, 0, {
                name: 'Link',
                field: 'supply_dash_url',
                checked: false,
                type: 'link',
                internal: $scope.isPermissionInternal('zemauth.supply_dash_link_view')
            });
        }

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.columns.splice($scope.columns.length - 1, 0, {
                name: 'Visits',
                field: 'visits',
                checked: true,
                type: 'number',
                help: 'The number of visits as reported by Google Analytics.',
                internal: $scope.isPermissionInternal('zemauth.postclick_metrics')
            });
        }

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.columns.splice($scope.columns.length - 1, 0, {
                name: 'Pageviews',
                field: 'pageviews',
                checked: true,
                type: 'number',
                help: 'The number of pageviews as reported by Google Analytics.',
                internal: $scope.isPermissionInternal('zemauth.postclick_metrics')
            });
        }

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.columns.splice($scope.columns.length - 1, 0, {
                name: '% New Users',
                field: 'percent_new_users',
                checked: false,
                type: 'percent',
                help: 'Percentage of visits made by new users, as reported by Google Analytics.',
                internal: $scope.isPermissionInternal('zemauth.postclick_metrics')
            });
        }

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.columns.splice($scope.columns.length - 1, 0, {
                name: 'Bounce Rate',
                field: 'bounce_rate',
                checked: false,
                type: 'percent',
                help: 'Bounce rate help goes here.',
                internal: $scope.isPermissionInternal('zemauth.postclick_metrics')
            });
        }

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.columns.splice($scope.columns.length - 1, 0, {
                name: 'PV/Visit',
                field: 'pv_per_visit',
                checked: false,
                type: 'number',
                fractionSize: 2,
                help: 'Help, pageviews per visit.',
                internal: $scope.isPermissionInternal('zemauth.postclick_metrics')
            });
        }

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.columns.splice($scope.columns.length - 1, 0, {
                name: 'Avg. ToS',
                field: 'avg_tos',
                checked: false,
                type: 'seconds',
                help: 'Help, average time on site.',
                internal: $scope.isPermissionInternal('zemauth.postclick_metrics')
            });
        }

        if ($scope.hasPermission('zemauth.postclick_metrics')) {
            $scope.columns.splice($scope.columns.length - 1, 0, {
                name: 'Click Discrepancy',
                field: 'click_discrepancy',
                checked: false,
                type: 'percent',
                help: 'Help, click discrepancy.',
                internal: $scope.isPermissionInternal('zemauth.postclick_metrics')
            });
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

    $scope.setChartData = function () {
        var result = {
            formats: [],
            data: [],
            names: [],
            ids: []
        };

        result.formats = [$scope.chartMetric1, $scope.chartMetric2].map(function (x) {
            var format = null;
            if (x === constants.sourceChartMetric.COST ||
                x === constants.sourceChartMetric.CPC) {
                format = 'currency';
            } else if (x === constants.sourceChartMetric.CTR) {
                format = 'percent';
            } else {
                // check goal metrics for format info
                $scope.sourceChartMetrics.forEach(function (metric) {
                    if (x === metric.value && metric.format) {
                        format = metric.format;
                    }
                });
            }

            return format;
        });

        var temp = {};
        var lastDate = null;
        var oneDayMs = 24*60*60*1000;
        $scope.dailyStats.forEach(function (stat) {
            if (!temp.hasOwnProperty(stat.sourceId)) {
                temp[stat.sourceId] = {
                    name: stat.sourceName,
                    id: stat.sourceId,
                    data: [[]]
                };
            }

            // insert nulls for missing values
            if (lastDate) {
                for (var date = lastDate; date < stat.date - oneDayMs; date += oneDayMs) {
                    temp[stat.sourceId].data[0].push([date, null]);

                    if (temp[stat.sourceId].data[1]) {
                        temp[stat.sourceId].data[1].push([date, null]);
                    }
                }
            }
            lastDate = stat.date;

            temp[stat.sourceId].data[0].push([stat.date, stat[$scope.chartMetric1]]);

            if ($scope.chartMetric2 && $scope.chartMetric2 !== $scope.chartMetric1) {
                if (!temp[stat.sourceId].data[1]) {
                    temp[stat.sourceId].data[1] = [];
                }
                temp[stat.sourceId].data[1].push([stat.date, stat[$scope.chartMetric2]]);
            }
        });

        Object.keys(temp).forEach(function (sourceId) {
            result.data.push(temp[sourceId].data);
            result.names.push(temp[sourceId].name);
            result.ids.push(temp[sourceId].id);
        });

        $scope.chartData = result;
    };

    $scope.loadRequestInProgress = false;

    $scope.orderRows = function (col) {
        if ($scope.order.indexOf(col) === 1) {
            $scope.order = col;
        } else if ($scope.order.indexOf(col) === -1 && col === 'name') {
            $scope.order = col;
        } else {
            $scope.order = '-' + col;
        }

        $location.search('order', $scope.order);
        localStorageService.set('adGroupSources.order', $scope.order);
        $scope.getTableData();
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
                            'help': 'Number of goal completions',
                            internal: $scope.isPermissionInternal('zemauth.postclick_metrics')
                        }
                        $scope.columns.splice($scope.columns.length - 1, 0, col_descr);
                    } else if(field.indexOf(': Conversion Rate') != -1) {
                        var col_descr = {
                            'name': field.substr('goal__'.length),
                            'field': field,
                            'checked': false,
                            'type': 'percent',
                            'help': 'Conversion rate help',
                            internal: $scope.isPermissionInternal('zemauth.postclick_metrics')
                        }
                        $scope.columns.splice($scope.columns.length - 1, 0, col_descr);
                    }
                }
            }
        }
    };

    $scope.getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.adGroupSourcesTable.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.addGoalColumns(data.rows);

                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;

                $scope.selectSources();
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };

    $scope.getDailyStats = function () {
        api.adGroupDailyStats.list($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedSourceIds, $scope.selectedSourceTotals).then(
            function (data) {
                $scope.dailyStats = data.stats;
                $scope.sourceChartMetrics = options.sourceChartMetrics.concat(data.options);
                $scope.setChartData();
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.updateSelectedSources = function (sourceId) {
        var i = $scope.selectedSourceIds.indexOf(sourceId);
        if (i > -1) {
            $scope.selectedSourceIds.splice(i, 1);
        } else {
            $scope.selectedSourceIds.push(sourceId);
        }
    };

    $scope.selectedSourceRemoved = function (sourceId) {
        if (sourceId) {
            $scope.updateSelectedSources(String(sourceId));
        } else {
            $scope.selectedSourceTotals = false;
        }

        $scope.selectSources();
        $scope.updateSelectedRowsData();
    };

    $scope.selectedSourcesChanged = function (sourceId) {
        if (sourceId) {
            $scope.updateSelectedSources(sourceId);
        }

        $scope.updateSelectedRowsData();
    };

    $scope.updateSelectedRowsData = function () {
        if (!$scope.selectedSourceTotals && !$scope.selectedSourceIds.length) {
            $scope.selectedSourceTotals = true;
        }

        $location.search('source_ids', $scope.selectedSourceIds.join(','));
        $location.search('source_totals', $scope.selectedSourceTotals ? 1 : null);

        $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);
        $scope.setAdGroupData('sourceTotals', $scope.selectedSourceTotals);

        $scope.getDailyStats();
    };

    $scope.toggleChart = function () {
        $scope.isChartShown = !$scope.isChartShown;
        $scope.chartBtnTitle = $scope.isChartShown ? 'Hide chart' : 'Show chart';
        $location.search('chart_hidden', !$scope.isChartShown ? '1' : null);
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.setChartData();
            $location.search('chart_metric1', $scope.chartMetric1);
            localStorageService.set('adGroupSources.chartMetric1', $scope.chartMetric1);
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.setChartData();
            $location.search('chart_metric2', $scope.chartMetric2);
            localStorageService.set('adGroupSources.chartMetric2', $scope.chartMetric2);
        }
    });

    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if(newValue === true && oldValue === false){
            pollSyncStatus();
        }
    });

    // From parent scope (mainCtrl).
    $scope.$watch('dateRange', function (newValue, oldValue) {
        $scope.getDailyStats();
        $scope.getTableData();
    });

    $scope.selectSources = function () {
        $scope.rows.forEach(function (x) {
            x.checked = $scope.selectedSourceIds.indexOf(x.id) > -1;
        });
    };

    $scope.init = function() {
        var chartMetric1 = $location.search().chart_metric1 || localStorageService.get('adGroupSources.chartMetric1') || $scope.chartMetric1;
        var chartMetric2 = $location.search().chart_metric2 || localStorageService.get('adGroupSources.chartMetric2') || $scope.chartMetric2;
        var chartHidden = $location.search().chart_hidden;
        var order = $location.search().order || localStorageService.get('adGroupSources.order') || $scope.order;
        var changed = false;

        var data = $scope.adGroupData[$state.params.id];
        var sourceIds = $location.search().source_ids || (data && data.sourceIds && data.sourceIds.join(','));
        var sourceTotals = $location.search().source_totals || (data && data.sourceTotals ? 1 : null);

        if (chartMetric1 !== undefined && $scope.chartMetric1 !== chartMetric1) {
            $scope.chartMetric1 = chartMetric1;
            $location.search('chart_metric1', chartMetric1);
            changed = true;
        }

        if (chartMetric2 !== undefined && $scope.chartMetric2 !== chartMetric2) {
            $scope.chartMetric2 = chartMetric2;
            $location.search('chart_metric2', chartMetric2);
            changed = true;
        }

        if (chartHidden) {
            $scope.isChartShown = false;
        }

        if (changed) {
            $scope.setChartData();
        }

        if (sourceIds) {
            $scope.selectedSourceIds = sourceIds.split(',');
            $scope.setAdGroupData('sourceIds', $scope.selectedSourceIds);
            $location.search('source_ids', sourceIds);

            if ($scope.rows) {
                $scope.selectSources();
            }
        }

        if (order !== undefined && $scope.order !== order) {
            $scope.order = order;
            $location.search('order', order);
        }

        $scope.selectedSourceTotals = !$scope.selectedSourceIds.length || !!sourceTotals;
        $scope.setAdGroupData('sourceTotals', $scope.selectedSourceTotals);
        $location.search('source_totals', sourceTotals);

        $scope.getAdGroupState();
        $scope.initColumns();

        $scope.getSources();
    };

    // export
    $scope.downloadReport = function() {
        $window.open('api/ad_groups/' + $state.params.id + '/sources/export/?type=' + $scope.exportType + '&start_date=' + $scope.dateRange.startDate.format() + '&end_date=' + $scope.dateRange.endDate.format(), '_blank');
        $scope.exportType = '';
    };

    $scope.getSources = function () {
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
                $scope.getSources();
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
                            $scope.getTableData();
                            $scope.getDailyStats();
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
