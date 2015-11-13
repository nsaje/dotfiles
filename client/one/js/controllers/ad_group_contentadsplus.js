/* globals oneApp, options, angular */
oneApp.controller('AdGroupAdsPlusCtrl', ['$scope', '$window', '$state', '$modal', '$location', '$q', 'api', 'zemUserSettings', '$timeout', 'zemFilterService', 'zemPostclickMetricsService', function($scope, $window, $state, $modal, $location, $q, api, zemUserSettings, $timeout, zemFilterService, zemPostclickMetricsService) {
    var contentAdsNotLoaded = $q.defer();

    $scope.order = '-upload_time';
    $scope.loadRequestInProgress = false;
    $scope.sizeRange = [5, 10, 20, 50];
    $scope.size = $scope.sizeRange[0];
    $scope.lastChangeTimeout = null;
    $scope.rows = null;
    $scope.totals = null;
    $scope.isIncompletePostclickMetrics = false;

    $scope.chartHidden = false;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartMetricOptions = options.adGroupChartMetrics;
    $scope.localStoragePrefix = 'adGroupContentAdsPlus';

    $scope.lastSyncDate = null;
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;

    $scope.selectionMenuConfig = {};

    // selection triplet - all, a batch, or specific content ads can be selected
    $scope.selectedAll = false;
    $scope.selectedBatchId = null;
    $scope.selectedContentAdsStatus = {};

    $scope.archivingResults = null;
    $scope.closeArchivingResults = function() {
        $scope.archivingResults = null;
    };

    $scope.pagination = {
        currentPage: 1
    };

    $scope.exportOptions = [{
        name: 'By Content Ad (CSV)',
        value: 'content-ad-csv'
    }, {
        name: 'By Content Ad (Excel)',
        value: 'content-ad-excel'
    }, {
        name: 'By Day (CSV)',
        value: 'day-csv'
    }, {
        name: 'By Day (Excel)',
        value: 'day-excel'
    }];

    $scope.exportPlusOptions = [
      {name: 'Current View', value: 'contentad-csv'}
    ];

    $scope.bulkActions = [{
        name: 'Pause',
        value: 'pause',
        hasPermission: $scope.hasPermission('zemauth.content_ads_bulk_actions')
    }, {
        name: 'Resume',
        value: 'resume',
        hasPermission: $scope.hasPermission('zemauth.content_ads_bulk_actions')
    }, {
        name: 'Download',
        value: 'download',
        hasPermission: $scope.hasPermission('zemauth.get_content_ad_csv')
    }, {
        name: 'Archive',
        value: 'archive',
        hasPermission: $scope.hasPermission('zemauth.archive_restore_entity'),
        internal: $scope.isPermissionInternal('zemauth.archive_restore_entity'),
        notification: 'All selected Content Ads will be paused and archived.'
    }, {
        name: 'Restore',
        value: 'restore',
        hasPermission: $scope.hasPermission('zemauth.archive_restore_entity'),
        internal: $scope.isPermissionInternal('zemauth.archive_restore_entity')
    }];

    $scope.selectedAdsChanged = function(row, checked) {
        $scope.selectedContentAdsStatus[row.id] = checked;

        var numSelected = 0,
            numNotSelected = 0;

        Object.keys($scope.selectedContentAdsStatus).forEach(function (contentAdId) {
            if ($scope.selectedContentAdsStatus[contentAdId]) {
                numSelected += 1;
            } else {
                numNotSelected += 1;
            }
        });

        if ($scope.selectedAll) {
            $scope.selectionMenuConfig.partialSelection = numNotSelected > 0;
        } else if (!$scope.selectedBatchId) {
            $scope.selectionMenuConfig.partialSelection = numSelected > 0;
        }
    };

    $scope.selectionMenuConfig.selectAllCallback = function (selected) {
        $scope.selectionMenuConfig.partialSelection = false;
        $scope.selectedAll = selected;
        $scope.selectedBatchId = null;
        $scope.selectedContentAdsStatus = {};

        if (selected) {
            $scope.updateContentAdSelection();
        } else {
            $scope.clearContentAdSelection();
        }
    };

    $scope.selectBatchCallback = function (id) {
        $scope.selectionMenuConfig.partialSelection = true;
        $scope.selectedAll = false;
        $scope.selectedBatchId = id;
        $scope.selectedContentAdsStatus = {};

        $scope.updateContentAdSelection();
    };

    $scope.clearContentAdSelection = function () {
        $scope.rows.forEach(function (row) {
            row.ad_selected = false;
        });
    };

    $scope.updateContentAdSelection = function() {
        $scope.rows.forEach(function(row) {
            if ($scope.selectedContentAdsStatus[row.id] !== undefined) {
                row.ad_selected = $scope.selectedContentAdsStatus[row.id];
            } else if ($scope.selectedAll) {
                row.ad_selected = true;
            } else if ($scope.selectedBatchId && row.batch_id == $scope.selectedBatchId) {
                row.ad_selected = true;
            } else {
                row.ad_selected = false;
            }
        });
    };

    $scope.isAnythingSelected = function() {
        if ($scope.selectedAll || $scope.selectedBatchId) {
            return true;
        }

        for (var contentAdId in $scope.selectedContentAdsStatus) {
            if ($scope.selectedContentAdsStatus.hasOwnProperty(contentAdId)
                    && $scope.selectedContentAdsStatus[contentAdId]) {
                return true;
            }
        }

        return false;
    };

    var updateContentAdStates = function (state) {
        $scope.rows.forEach(function (row) {
            if (row.ad_selected) {
                row.status_setting = state;
            }
        });
    };

    $scope.columns = [{
        name: '',
        field: 'ad_selected',
        type: 'checkbox',
        showSelectionMenu: true,
        shown: $scope.hasPermission('zemauth.content_ads_bulk_actions'),
        hasPermission: $scope.hasPermission('zemauth.content_ads_bulk_actions'),
        checked: true,
        totalRow: false,
        unselectable: true,
        order: false,
        selectCallback: $scope.selectedAdsChanged,
        disabled: false,
        selectionMenuConfig: $scope.selectionMenuConfig
    }, {
        name: 'Thumbnail',
        nameCssClass: 'table-name-hidden',
        field: 'image_urls',
        checked: true,
        type: 'image',
        shown: true,
        totalRow: false,
        titleField: 'title',
        order: false
    }, {
        name: '\u25CF',
        field: 'status_setting',
        type: 'state',
        order: true,
        initialOrder: 'asc',
        enabledValue: constants.contentAdSourceState.ACTIVE,
        pausedValue: constants.contentAdSourceState.INACTIVE,
        internal: $scope.isPermissionInternal('zemauth.set_content_ad_status'),
        shown: $scope.hasPermission('zemauth.set_content_ad_status'),
        checked: true,
        totalRow: false,
        unselectable: true,
        help: 'A setting for enabling and pausing content ads.',
        onChange: function (contentAdId, state) {
            api.adGroupContentAdState.save($state.params.id, state, [contentAdId]).then(
                function () {
                    $scope.pollTableUpdates();
                }
            );
        },
        getDisabledMessage: function(row) {
            return 'This ad must be managed manually.';
        },
        disabled: false,
        archivedField: 'archived'
    }, {
        name: 'Status',
        field: 'submission_status',
        checked: false,
        type: 'submissionStatus',
        archivedField: 'archived',
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
        help: 'The creative title/headline of a content ad. The link to landing page includes tracking codes.',
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
        name: 'Display URL',
        field: 'display_url',
        checked: false,
        extraTdCss: 'no-wrap',
        type: 'text',
        shown: true,
        help: 'Advertiser\'s display URL.',
        totalRow: false,
        titleField: 'display_url',
        order: true,
        orderField: 'display_url',
        initialOrder: 'asc'
    }, {
        name: 'Brand Name',
        field: 'brand_name',
        checked: false,
        extraTdCss: 'no-wrap',
        type: 'text',
        shown: true,
        help: 'Advertiser\'s brand name',
        totalRow: false,
        titleField: 'brand_name',
        order: true,
        orderField: 'brand_name',
        initialOrder: 'asc'
    }, {
        name: 'Description',
        field: 'description',
        checked: false,
        extraTdCss: 'no-wrap',
        type: 'text',
        shown: true,
        help: 'Description of a content ad.',
        totalRow: false,
        titleField: 'description',
        order: true,
        orderField: 'description',
        initialOrder: 'asc'
    }, {
        name: 'Call to action',
        field: 'call_to_action',
        checked: false,
        extraTdCss: 'no-wrap',
        type: 'text',
        shown: true,
        help: 'Call to action text.',
        totalRow: false,
        titleField: 'call_to_action',
        order: true,
        orderField: 'call_to_action',
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
    }, {
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
    }];

    $scope.columnCategories = [{
        'name': 'Content Sync',
        'fields': ['ad_selected', 'image_urls', 'titleLink', 'urlLink', 'submission_status', 'checked', 'upload_time', 'batch_name', 'display_url', 'brand_name', 'description', 'call_to_action']
    }, {
        'name': 'Traffic Acquisition',
        'fields': ['cost', 'cpc', 'clicks', 'impressions', 'ctr']
    }, {
        'name': 'Audience Metrics',
        'fields': ['percent_new_users', 'bounce_rate', 'pv_per_visit', 'avg_tos', 'visits', 'pageviews', 'click_discrepancy']
    }, {
        name: 'Conversions',
        fields: ['conversion_goal_1', 'conversion_goal_2']
    }];

    $scope.addContentAds = function() {
        var modalInstance = $modal.open({
            templateUrl: '/partials/upload_ads_modal.html',
            controller: 'UploadAdsModalCtrl',
            windowClass: 'modal',
            scope: $scope
        });

        modalInstance.result.then(function() {
            getTableData();
        });

        return modalInstance;
    };

    var bulkUpdateContentAds = function (contentAdIdsSelected, contentAdIdsNotSelected, state) {
        updateContentAdStates(state);

        api.adGroupContentAdState.save(
            $state.params.id,
            state,
            contentAdIdsSelected,
            contentAdIdsNotSelected,
            $scope.selectedAll,
            $scope.selectedBatchId
        ).then(function () {
            $scope.pollTableUpdates();
        });
    };

    $scope.updateTableAfterArchiving = function(data) {
        // update rows immediately, refresh whole table after
        updateTableData(data.data.rows, {});

        if (!isNaN(data.data.archived_count) && !isNaN(data.data.active_count)) {
            $scope.archivingResults = {
                archived_count: data.data.archived_count,
                active_count: data.data.active_count
            };
        }
        else {
            $scope.archivingResults = null;
        }

        if (!zemFilterService.getShowArchived()) {
            $scope.selectedAll = false;
            $scope.selectedBatchId = null;
            $scope.selectedContentAdsStatus = {};
            getTableData();
            getDailyStats();
        }
    };

    var downloadContentAds = function (contentAdIdsSelected, contentAdIdsNotSelected) {
        var url = '/api/ad_groups/' + $state.params.id + '/contentads/csv/?';

        url += 'content_ad_ids_selected=' + contentAdIdsSelected.join(',');
        url += '&content_ad_ids_not_selected=' + contentAdIdsNotSelected.join(',');
        url += '&archived=' + zemFilterService.getShowArchived();

        if ($scope.selectedAll) {
            url += '&select_all=' + $scope.selectedAll;
        }

        if ($scope.selectedBatchId) {
            url += '&select_batch=' + $scope.selectedBatchId;
        }

        $window.open(url, '_blank');
    };

    $scope.executeBulkAction = function (action) {

        if (!$scope.isAnythingSelected()) {
            return;
        }

        var contentAdIdsSelected = [],
            contentAdIdsNotSelected = [];

        Object.keys($scope.selectedContentAdsStatus).forEach(function (contentAdId) {
            if ($scope.selectedContentAdsStatus[contentAdId]) {
                contentAdIdsSelected.push(contentAdId);
            } else {
                contentAdIdsNotSelected.push(contentAdId);
            }
        });

        switch (action) {
            case 'pause':
                bulkUpdateContentAds(
                    contentAdIdsSelected,
                    contentAdIdsNotSelected,
                    constants.contentAdSourceState.INACTIVE
                );
                break;
            case 'resume':
                bulkUpdateContentAds(
                    contentAdIdsSelected,
                    contentAdIdsNotSelected,
                    constants.contentAdSourceState.ACTIVE
                );
                break;
            case 'download':
                downloadContentAds(contentAdIdsSelected, contentAdIdsNotSelected);
                break;
            case 'archive':
                api.adGroupContentAdArchive.archive(
                    $state.params.id,
                    contentAdIdsSelected,
                    contentAdIdsNotSelected,
                    $scope.selectedAll,
                    $scope.selectedBatchId).then($scope.updateTableAfterArchiving);
                break;
            case 'restore':
                api.adGroupContentAdArchive.restore(
                    $state.params.id,
                    contentAdIdsSelected,
                    contentAdIdsNotSelected,
                    $scope.selectedAll,
                    $scope.selectedBatchId).then($scope.updateTableAfterArchiving);
                break;
        }
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
    $scope.$watch('dateRange', function(newValue, oldValue) {
        if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
            return;
        }

        getDailyStats();
        getTableData();
    });

    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if (newValue === true && oldValue === false) {
            pollSyncStatus();
        }
    });

    var hasMetricData = function(metric) {
        var hasData = false;
        $scope.chartData.forEach(function(group) {
            if (group.seriesData[metric] !== undefined) {
                hasData = true;
            }
        });

        return hasData;
    };

    $scope.$watch('chartMetric1', function(newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!hasMetricData($scope.chartMetric1)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    $scope.$watch('chartMetric2', function(newValue, oldValue) {
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

    $scope.toggleChart = function() {
        $scope.chartHidden = !$scope.chartHidden;

        $timeout(function() {
            $scope.$broadcast('highchartsng.reflow');
        }, 0);
    };

    $scope.$watch(zemFilterService.getFilteredSources, function(newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }
        getTableData();
        getDailyStats();
    }, true);

    $scope.$watch(zemFilterService.getShowArchived, function(newValue, oldValue) {
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

    var getTableData = function() {
        $scope.loadRequestInProgress = true;

        api.adGroupAdsPlusTable.get($state.params.id, $scope.pagination.currentPage, $scope.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function(data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.order = data.order;
                $scope.pagination = data.pagination;
                $scope.notifications = data.notifications;
                $scope.lastChange = data.lastChange;

                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;
                $scope.dataStatus = data.dataStatus;

                $scope.pollTableUpdates();
                $scope.updateContentAdSelection();

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;
                zemPostclickMetricsService.setConversionGoalColumnsDefaults($scope.columns, data.conversionGoals, $scope.hasPermission('zemauth.conversion_reports'));

                initUploadBatches(data.batches);
                contentAdsNotLoaded.resolve($scope.rows.length === 0);
            },
            function(data) {
                // error
                return;
            }
        ).finally(function() {
            $scope.loadRequestInProgress = false;
        });
    };

    var pollSyncStatus = function() {
        if ($scope.isSyncInProgress) {
            $timeout(function() {
                api.checkSyncProgress.get($state.params.id).then(
                    function(data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if ($scope.isSyncInProgress === false) {
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
        zemPostclickMetricsService.insertAcquisitionColumns(
            $scope.columns,
            $scope.columns.length - 2,
            $scope.hasPermission('zemauth.content_ads_postclick_acquisition'),
            $scope.isPermissionInternal('zemauth.content_ads_postclick_acquisition')
        );

        zemPostclickMetricsService.insertEngagementColumns(
            $scope.columns,
            $scope.columns.length - 2,
            $scope.hasPermission('zemauth.content_ads_postclick_engagement'),
            $scope.isPermissionInternal('zemauth.content_ads_postclick_engagement')
        );

        zemPostclickMetricsService.insertConversionGoalColumns(
            $scope.columns,
            $scope.columns.length - 2,
            $scope.hasPermission('zemauth.conversion_reports'),
            $scope.isPermissionInternal('zemauth.conversion_reports')
        );
    };

    var initUploadBatches = function (batches) {
        $scope.selectionMenuConfig.selectionOptions = [{
            type: 'link-list',
            name: 'Upload batch',
            callback: $scope.selectBatchCallback,
            items: batches
        }];
    };

    var init = function () {
        if (!$scope.adGroup.contentAdsTabWithCMS && !$scope.hasPermission('zemauth.new_content_ads_tab')) {
            $state.go('main.adGroups.ads', {
                id: $scope.adGroup.id
            });
            return;
        }

        var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);
        var page = parseInt($location.search().page || '1');
        var size = parseInt($location.search().size || '0');

        setChartOptions();

        userSettings.registerWithoutWatch('chartMetric1');
        userSettings.registerWithoutWatch('chartMetric2');
        userSettings.register('order');
        userSettings.register('size');

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
            $location.search('page', page);
        }

        if (size !== 0 && $scope.size !== size) {
            $scope.size = size;
        }
        // if nothing in local storage or page query var set first as default
        if ($scope.size === 0) {
            $scope.size = $scope.sizeRange[0];
        }
        getTableData();
        getDailyStats();
        $scope.getAdGroupState();
        initColumns();

        pollSyncStatus();
        setDisabledExportOptions();
    };

    $scope.pollTableUpdates = function () {
        if ($scope.lastChangeTimeout) {
            return;
        }

        api.adGroupAdsPlusTable.getUpdates($state.params.id, $scope.lastChange)
            .then(function(data) {
                if (data.lastChange) {
                    $scope.lastChange = data.lastChange;
                    $scope.notifications = data.notifications;

                    $scope.updateDataStatus(data.dataStatus);
                    updateTableData(data.rows, data.totals);
                }

                if (data.inProgress) {
                    $scope.lastChangeTimeout = $timeout(function() {
                        $scope.lastChangeTimeout = null;
                        $scope.pollTableUpdates();
                    }, 2000);
                }
            });
    };

    $scope.canShowOnboardingGuidance = function () {
        return contentAdsNotLoaded.promise;
    };

    var updateTableData = function(rowsUpdates, totalsUpdates) {
        $scope.rows.forEach(function(row) {
            var rowUpdates = rowsUpdates[row.id];
            if (rowUpdates) {
                updateObject(row, rowUpdates);
            }
        });

        updateObject($scope.totals, totalsUpdates);
    };

    $scope.updateDataStatus = function(newDataStatus) {
        for (var rowid in newDataStatus) {
            var newStatus = newDataStatus[rowid];
            if (newStatus) {
                $scope.dataStatus[rowid] = newStatus;
            }
        };
    };

    var updateObject = function(object, updates) {
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


    var getDailyStats = function() {
        api.dailyStats.listContentAdStats($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, getDailyStatsMetrics()).then(
            function(data) {
                setConversionGoalChartOptions(data.conversionGoals);
                $scope.chartData = data.chartData;
            },
            function(data) {
                // error
                return;
            }
        );
    };

    var setChartOptions = function () {
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
        }

        if ($scope.hasPermission('zemauth.conversion_reports')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                options.adGroupConversionGoalChartMetrics,
                $scope.isPermissionInternal('zemauth.conversion_reports')
            );
        }
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

    var setDisabledExportOptions = function() {
        api.adGroupAdsPlusExportAllowed.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate).then(
            function(data) {
                var option = null;
                $scope.exportOptions.forEach(function(opt) {
                    if (opt.value === 'day-excel') {
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
