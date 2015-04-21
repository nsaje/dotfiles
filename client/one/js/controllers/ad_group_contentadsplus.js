/* globals oneApp, options */
oneApp.controller('AdGroupAdsPlusCtrl', ['$scope', '$state', '$modal', '$location', 'api', 'zemUserSettings', 'zemCustomTableColsService', '$timeout', 'zemFilterService', function ($scope, $state, $modal, $location, api, zemUserSettings, zemCustomTableColsService, $timeout, zemFilterService) {
    $scope.order = '-upload_time';
    $scope.loadRequestInProgress = false;
    $scope.selectedColumnsCount = 0;
    $scope.sizeRange = [5, 10, 20, 50];
    $scope.size = $scope.sizeRange[0];
    $scope.lastChangeTimeout = null;
    $scope.rows = null;
    $scope.totals = null;

    $scope.chartHidden = false;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = options.adGroupChartMetrics;

    $scope.lastSyncDate = null;
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;

    $scope.pagination = {
        currentPage: 1
    };

    $scope.exportOptions = [
        {name: 'CSV by day', value: 'csv'},
        {name: 'Excel by day', value: 'excel'}
    ];

    $scope.columns = [
        {
            name: 'Thumbnail',
            nameCssClass: 'table-name-hidden',
            field: 'image_urls',
            checked: true,
            type: 'image',
            shown: true,
            totalRow: false,
            titleField: 'title',
            order: false,
        }, {
            name: '',
            nameCssClass: 'active-circle-icon-gray',
            field: 'status_setting',
            type: 'state',
            enabledValue: constants.contentAdSourceState.ACTIVE,
            pausedValue: constants.contentAdSourceState.INACTIVE,
            internal: $scope.isPermissionInternal('zemauth.new_content_ads_tab'),
            shown: $scope.hasPermission('zemauth.new_content_ads_tab'),
            checked: true,
            totalRow: false,
            unselectable: true,
            help: 'A setting for enabling and pausing content ads.',
            onChange: function (sourceId, state) {
                api.adGroupContentAdState.save($state.params.id, sourceId, state).then(
                    function () {
                        pollTableUpdates();
                    }
                );
            },
            getDisabledMessage: function (row) {
                return 'This ad must be managed manually.';
            },
            disabled: false
        }, {
            name: 'Status',
            field: 'submission_status',
            checked: true,
            type: 'submissionStatus',
            shown: true,
            help: 'Current submission status.',
            totalRow: false,
        }, {
            name: '',
            unselectable: true,
            checked: true,
            type: 'notification',
            shown: true,
            totalRow: false,
            extraTdCss: 'notification-no-text'
        }, {
            name: 'Title',
            field: 'titleLink',
            checked: true,
            type: 'linkText',
            shown: true,
            totalRow: false,
            help: 'The creative title/headline of a content ad.',
            extraTdCss: 'trimmed title',
            titleField: 'title',
            order: true,
            orderField: 'title',
            initialOrder: 'asc'
        }, {
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
        }, {
            name: 'Uploaded',
            field: 'upload_time',
            checked: true,
            type: 'datetime',
            shown: true,
            help: 'The time when the content ad was uploaded.',
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Batch Name',
            field: 'batch_name',
            checked: true,
            extraTdCss: 'no-wrap',
            type: 'text',
            shown: true,
            help: 'The name of the upload batch.',
            totalRow: false,
            titleField: 'batch_name',
            order: true,
            orderField: 'batch_name',
            initialOrder: 'asc'
        }, {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            shown: true,
            help: "The amount spent per content ad.",
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            shown: true,
            fractionSize: 3,
            help: "The average CPC for each content ad.",
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
            shown: true,
            help: 'The number of times a content ad has been clicked.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number',
            shown: true,
            help: 'The number of times a content ad has been displayed.',
            totalRow: true,
            order: true,
            initialOrder: 'desc'
        }, {
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

    $scope.columnCategories = [{
        'name': 'Content Sync',
        'fields': ['image_urls' ,'titleLink', 'submission_status', 'urlLink', 'upload_time', 'batch_name']
    }, {
        'name': 'Traffic Acquisition',
        'fields': ['cost', 'cpc', 'clicks', 'impressions', 'ctr']
    }];

    $scope.addContentAds = function() {
        var modalInstance = $modal.open({
            templateUrl: '/partials/upload_ads_modal.html',
            controller: 'UploadAdsModalCtrl',
            windowClass: 'upload-ads-modal',
            scope: $scope,
            resolve: {
                errors: ['api', function(api) {
                    return api.adGroupAdsPlusUpload.validateSettings($state.params.id);
                }]
            }
        });

        modalInstance.result.then(function () {
            getTableData();
        });

        return modalInstance;
    };

    $scope.loadPage = function(page) {
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

    $scope.$watch('size', function(newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.loadPage();
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

    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if(newValue === true && oldValue === false){
            pollSyncStatus();
        }
    });

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

    $scope.orderTableData = function(order) {
        $scope.order = order;

        $location.search('order', $scope.order);
        getTableData();
    };

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;

        $timeout(function() {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        getTableData();
        getDailyStats();
    }, true);

    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;
        api.adGroupSync.get($state.params.id);
    };

    var getTableData = function () {
        $scope.loadRequestInProgress = true;

        api.adGroupAdsPlusTable.get($state.params.id, $scope.pagination.currentPage, $scope.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.order = data.order;
                $scope.pagination = data.pagination;
                $scope.notifications = data.notifications;
                $scope.lastChange = data.lastChange;

                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                pollTableUpdates();
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
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

    var initColumns = function () {
        var cols;

        cols = zemCustomTableColsService.load('adGroupAdsPlus', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('adGroupAdsPlus', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    var init = function() {
        var userSettings = zemUserSettings.getInstance($scope, 'adGroupContentAdsPlus');
        var page = $location.search().page;

        userSettings.register('order');
        userSettings.register('size');

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
            $scope.setAdGroupData('page', page);
            $location.search('page', page);
        }

        getTableData();
        getDailyStats();
        $scope.getAdGroupState();
        initColumns();

        pollSyncStatus();
        setDisabledExportOptions();
    };

    var pollTableUpdates = function () {
        if ($scope.lastChangeTimeout) {
            return;
        }

        api.adGroupAdsPlusTable.getUpdates($state.params.id, $scope.lastChange)
            .then(function (data) {
                if (data.lastChange) {
                    $scope.lastChange = data.lastChange;
                    $scope.notifications = data.notifications;

                    updateTableData(data.rows, data.totals);
                }

                if (data.inProgress) {
                    $scope.lastChangeTimeout = $timeout(function () {
                        $scope.lastChangeTimeout = null;
                        pollTableUpdates();
                    }, 2000);
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

    var getDailyStats = function () {
        api.dailyStats.listContentAdStats($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, getDailyStatsMetrics()).then(
            function (data) {
                $scope.chartData = data.chartData;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    var setDisabledExportOptions = function() {
        api.adGroupAdsPlusExportAllowed.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate).then(
            function (data) {
                var option = null;
                $scope.exportOptions.forEach(function (opt) {
                    if (opt.value === 'excel') {
                        option = opt;
                    }
                });

                option.disabled = false;
                if (!data.allowed) {
                    option.disabled = true;
                    option.maxDays = data.maxDays;
                }
            }
        );
    };

    init();
}]);
