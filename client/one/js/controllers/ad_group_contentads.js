/*globals oneApp,moment,constants,options*/
oneApp.controller('AdGroupAdsCtrl', ['$scope', '$state', '$location', '$timeout', 'api', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', function ($scope, $state, $location, $timeout, api, zemPostclickMetricsService, zemFilterService, zemUserSettings) {
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.order = '-cost';
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartHidden = false;
    $scope.chartMetricOptions = options.adGroupChartMetrics;
    $scope.chartGoalMetrics = null;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.isIncompletePostclickMetrics = false;
    $scope.sizeRange = [5, 10, 20, 50];
    $scope.size = $scope.sizeRange[0];
    $scope.localStoragePrefix = 'adGroupAds';

    $scope.pagination = {
        currentPage: 1
    };

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    $scope.exportOptions = [
        {name: 'By Day (CSV)', value: 'csv'},
        {name: 'By Day (Excel)', value: 'excel'}
    ];

    $scope.columns = [
        {
            name: 'Title',
            field: 'titleLink',
            unselectable: true,
            checked: true,
            type: 'linkText',
            shown: true,
            hasTotalsLabel: true,
            totalRow: false,
            help: 'The creative title/headline of a content ad.',
            extraTdCss: 'trimmed title',
            titleField: 'title',
            order: true,
            orderField: 'title',
            initialOrder: 'asc'
        },
        {
            name: 'URL',
            field: 'urlLink',
            checked: true,
            type: 'linkText',
            shown: true,
            help: 'The web address of the content ad.',
            extraTdCss: 'trimmed url',
            totalRow: false,
            titleField: 'url',
            order: true,
            orderField: 'url',
            initialOrder: 'asc'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            shown: true,
            help: 'The amount spent per creative.',
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
            help: 'The average CPC for each content ad.',
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
            help: 'The number of clicks divided by the number of impressions.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }
    ];

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
                'urlLink', 'cost', 'cpc', 'clicks', 'impressions', 'ctr'
            ]
        },
        {
            'name': 'Audience Metrics',
            'fields': [
                'visits', 'pageviews', 'percent_new_users',
                'bounce_rate', 'pv_per_visit', 'avg_tos',
                'click_discrepancy'
            ]
        }
    ];

    var initColumns = function () {
        zemPostclickMetricsService.insertAcquisitionColumns(
            $scope.columns,
            $scope.columns.length - 1,
            $scope.hasPermission('zemauth.content_ads_postclick_acquisition'),
            $scope.isPermissionInternal('zemauth.content_ads_postclick_acquisition')
        );

        zemPostclickMetricsService.insertEngagementColumns(
            $scope.columns,
            $scope.columns.length - 1,
            $scope.hasPermission('zemauth.content_ads_postclick_engagement'),
            $scope.isPermissionInternal('zemauth.content_ads_postclick_engagement')
        );
    };

    $scope.loadRequestInProgress = false;

    var getTableData = function () {
        $scope.loadRequestInProgress = true;

        api.adGroupAdsTable.get($state.params.id, $scope.pagination.currentPage, $scope.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                if ($scope.hasPermission('zemauth.content_ads_postclick_engagement')) {
                    zemPostclickMetricsService.insertConversionGoalColumns(
                        $scope.columns,
                        $scope.columns.length - 1,
                        data.rows,
                        $scope.columnCategories[1],
                        $scope.isPermissionInternal('zemauth.content_ads_postclick_engagement')
                    );
                }

                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;

                $scope.order = data.order;
                $scope.pagination = data.pagination;
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };

    $scope.orderTableData = function (order) {
        $scope.order = order;

        $location.search('order', $scope.order);
        getTableData();
    };

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

    var setChartOptions = function (goals) {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

        if ($scope.hasPermission('zemauth.content_ads_postclick_acquisition')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatAcquisitionChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.content_ads_postclick_acquisition')
            );
        }

        if ($scope.hasPermission('zemauth.content_ads_postclick_engagement')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatEngagementChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.content_ads_postclick_engagement')
            );

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
                        internal: $scope.isPermissionInternal('zemauth.content_ads_postclick_engagement')
                    };
                }).filter(function (option) {
                    return option !== undefined;
                }));
            }
        }

    };

    var getDailyStats = function () {
        api.dailyStats.list($scope.level, $state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, null, true, getDailyStatsMetrics(), null).then(
            function (data) {
                setChartOptions(data.goals);
                $scope.chartData = data.chartData;
                $scope.chartGoalMetrics = data.goals;
            },
            function (data) {
                // error
                return;
            }
        );
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
        $scope.chartData.forEach(function (group) {
            if (group.seriesData[metric] !== undefined) {
                hasData = true;
            }
        });

        return hasData;
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
        setDisabledExportOptions();
    });

    $scope.init = function () {
        if ($scope.adGroup.contentAdsTabWithCMS) {
            $state.go('main.adGroups.adsPlus', {id: $scope.adGroup.id});
            return;
        }

        var data = $scope.adGroupData[$state.params.id];

        var page = parseInt($location.search().page);
        if (isNaN(page)) {
            page = data && data.page;
        }
        var size = parseInt($location.search().size || '0');

        userSettings.register('order');
        userSettings.register('size');
        userSettings.registerGlobal('chartHidden');

        if (size !== 0 && $scope.size !== size) {
            $scope.size = size;
        }
        // if nothing in local storage or page query var set first as default
        if ($scope.size === 0) {
            $scope.size = $scope.sizeRange[0];
        }

        setChartOptions();

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
            $scope.setAdGroupData('page', page);
            $location.search('page', page);
        }

        $scope.loadPage();
        getDailyStats();
        getTableData();
        initColumns();
        setDisabledExportOptions();
    };

    $scope.loadPage = function (page) {
        if (page && page > 0 && page <= $scope.pagination.numPages) {
            $scope.pagination.currentPage = page;
        }

        if ($scope.pagination.currentPage && $scope.pagination.size) {
            $location.search('page', $scope.pagination.currentPage);
            $scope.setAdGroupData('page', $scope.pagination.currentPage);

            getTableData();
            $scope.getAdGroupState();
        }
    };

    $scope.$watch('size', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.loadPage();
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

    var setDisabledExportOptions = function () {
        api.adGroupAdsExportAllowed.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate).then(
            function (data) {
                var option = null;
                $scope.exportOptions.forEach(function (opt) {
                    if (opt.value === 'excel') {
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

    // trigger sync
    $scope.triggerSync = function () {
        $scope.isSyncInProgress = true;
        api.adGroupSync.get($state.params.id);
    };

    $scope.init();
}]);
