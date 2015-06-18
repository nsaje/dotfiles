/* globals oneApp, options, angular */
oneApp.controller('AdGroupAdsPlusCtrl', ['$scope', '$window', '$state', '$compile', '$modal', '$location', 'api', 'zemUserSettings', 'zemCustomTableColsService', '$timeout', 'zemFilterService', function($scope, $window, $state, $compile, $modal, $location, api, zemUserSettings, zemCustomTableColsService, $timeout, zemFilterService) {
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

    $scope.selectedBulkAction = null;
    $scope.selectionMenuConfig = {};

    // selection triplet - all, a batch, or specific content ads can be selected
    $scope.selectedAll = false;
    $scope.selectedBatchId = null;
    $scope.selectedContentAdsStatus = {};

    $scope.notification = null;
    $scope.closeAlert = function(index) {
        $scope.notification = null;
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

    $scope.bulkActions = [];

    var setBulkActions = function() {
        $scope.bulkActions.push({
            name: 'Pause',
            value: 'pause'
        }, {
            name: 'Resume',
            value: 'resume'
        }, {
            name: 'Download',
            value: 'download'
        });

        var archivePermission = 'zemauth.archive_restore_entity';
        if ($scope.hasPermission(archivePermission)) {
            $scope.bulkActions.push({
                name: 'Archive',
                value: 'archive',
                internal: $scope.isPermissionInternal(archivePermission),
                notification: 'All selected Content Ads will be paused and archived.'
            }, {
                name: 'Restore',
                value: 'restore',
                internal: $scope.isPermissionInternal(archivePermission)
            });

        }
    };

    var formatBulkActionsResult = function(object) {
        var bulkAction;
        $scope.bulkActions.forEach(function(bk) {
            if (bk.value == object.id) {
                bulkAction = bk;
            }
        });

        var notification = bulkAction.notification;
        var element = angular.element(document.createElement('span'));;
        if (notification) {
            element.attr('popover', notification);
            element.attr('popover-trigger', 'mouseenter');
            element.attr('popover-placement', 'right');
            element.attr('popover-append-to-body', 'true');

            // hide immediately without animation - solves a glitch when
            // the element is selected
            element.attr('popover-animation', 'false');
            element.on('$destroy', function() {
                element.trigger('mouseleave');
            });
        }

        element.text(object.text);

        if (bulkAction.internal !== undefined) {
            var internal = $compile(angular.element(document.createElement('zem-internal-feature')))($scope);
            element.append(internal);
        }

        return $compile(element)($scope);
    };

    $scope.bulkActionsConfig = {
        minimumResultsForSearch: -1,
        dropdownCssClass: 'show-rows',
        formatResult: formatBulkActionsResult
    };

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

    var updateContentAdStates = function (state, updateAll) {
        $scope.rows.forEach(function (row) {
            if (updateAll || row.ad_selected) {
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
        order: false,
    }, {
        name: '',
        nameCssClass: 'active-circle-icon-gray',
        field: 'status_setting',
        type: 'state',
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
    }, {
        name: 'Display URL',
        field: 'display_url',
        checked: true,
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
        checked: true,
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
        checked: true,
        extraTdCss: 'no-wrap',
        type: 'text',
        shown: true,
        help: 'Description of the ad group.',
        totalRow: false,
        titleField: 'description',
        order: true,
        orderField: 'description',
        initialOrder: 'asc'
    }, {
        name: 'Call to action',
        field: 'call_to_action',
        checked: true,
        extraTdCss: 'no-wrap',
        type: 'text',
        shown: true,
        help: 'Call to action text.',
        totalRow: false,
        titleField: 'call_to_action',
        order: true,
        orderField: 'call_to_action',
        initialOrder: 'asc'
    }];

    $scope.columnCategories = [{
        'name': 'Content Sync',
        'fields': ['ad_selected', 'image_urls', 'titleLink', 'submission_status', 'checked', 'upload_time', 'batch_name', 'display_url', 'brand_name', 'description', 'call_to_action']
    }, {
        'name': 'Traffic Acquisition',
        'fields': ['cost', 'cpc', 'clicks', 'impressions', 'ctr']
    }];

    $scope.addContentAds = function() {
        var modalInstance = $modal.open({
            templateUrl: '/partials/upload_ads_modal.html',
            controller: 'UploadAdsModalCtrl',
            windowClass: 'upload-ads-modal',
            scope: $scope
        });

        modalInstance.result.then(function() {
            getTableData();
        });

        return modalInstance;
    };

    var bulkUpdateContentAds = function (contentAdIdsSelected, contentAdIdsNotSelected, state) {
        updateContentAdStates(state, $scope.selectedAll);

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

    $scope.bulkArchiveContentAds = function (contentAdIdsSelected, contentAdIdsNotSelected) {
        api.adGroupContentAdArchive.archive(
            $state.params.id,
            contentAdIdsSelected,
            contentAdIdsNotSelected,
            $scope.selectedAll,
            $scope.selectedBatchId).then($scope.updateTableAfterArchiving);
    };

    $scope.bulkRestoreContentAds = function (contentAdIdsSelected, contentAdIdsNotSelected) {
        api.adGroupContentAdArchive.restore(
            $state.params.id,
            contentAdIdsSelected,
            contentAdIdsNotSelected,
            $scope.selectedAll,
            $scope.selectedBatchId).then($scope.updateTableAfterArchiving);
    };

    $scope.updateTableAfterArchiving = function(data) {
        // update rows immediately, refresh whole table after
        updateTableData(data.data.rows, {});

        if (data.data.notification) {
            $scope.notification = data.data.notification;
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

        if ($scope.selectedAll) {
            url += '&select_all=' + ($scope.selectedAll);
        }

        if ($scope.selectedBatchId) {
            url += '&select_batch=' + $scope.selectedBatchId;
        }

        $window.open(url, '_blank');
    };

    $scope.executeBulkAction = function () {

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

        switch ($scope.selectedBulkAction) {
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
                $scope.bulkArchiveContentAds(contentAdIdsSelected, contentAdIdsNotSelected);
                break;
            case 'restore':
                $scope.bulkRestoreContentAds(contentAdIdsSelected, contentAdIdsNotSelected);
                break;
        }

        $scope.selectedBulkAction = null;
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
        setDisabledExportOptions();
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

                $scope.pollTableUpdates();
                $scope.updateContentAdSelection();
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
        var cols;

        cols = zemCustomTableColsService.load('adGroupAdsPlus', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function(newValue, oldValue) {
            cols = zemCustomTableColsService.save('adGroupAdsPlus', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    var initUploadBatches = function () {
        api.adGroupAdsPlusUploadBatches.list($state.params.id).then(function (data) {
            $scope.selectionMenuConfig.selectionOptions = [{
                type: 'link-list',
                name: 'Upload batch',
                callback: $scope.selectBatchCallback,
                items: data.data.batches
            }];
        });
    };

    var init = function () {
        if (!$scope.adGroup.contentAdsTabWithCMS && !$scope.hasPermission('zemauth.new_content_ads_tab')) {
            $state.go('main.adGroups.ads', {
                id: $scope.adGroup.id
            });
            return;
        }
        var userSettings = zemUserSettings.getInstance($scope, 'adGroupContentAdsPlus');
        var page = parseInt($location.search().page || '1');

        userSettings.register('order');
        userSettings.register('size');

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
            $location.search('page', page);
        }
        getTableData();
        getDailyStats();
        $scope.getAdGroupState();
        initColumns();
        initUploadBatches();
        pollSyncStatus();
        setDisabledExportOptions();

        setBulkActions();
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

    var updateTableData = function(rowsUpdates, totalsUpdates) {
        $scope.rows.forEach(function(row) {
            var rowUpdates = rowsUpdates[row.id];
            if (rowUpdates) {
                updateObject(row, rowUpdates);
            }
        });

        updateObject($scope.totals, totalsUpdates);
    };

    var updateObject = function(object, updates) {
        for (var key in updates) {
            if (updates.hasOwnProperty(key)) {
                object[key] = updates[key];
            }
        }
    };

    var getDailyStatsMetrics = function() {
        var values = $scope.chartMetricOptions.map(function(option) {
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

    var getDailyStats = function() {
        api.dailyStats.listContentAdStats($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, getDailyStatsMetrics()).then(
            function(data) {
                $scope.chartData = data.chartData;
            },
            function(data) {
                // error
                return;
            }
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
