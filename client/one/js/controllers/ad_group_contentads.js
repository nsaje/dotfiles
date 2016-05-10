/* globals oneApp, options, angular, constants */
oneApp.controller('AdGroupAdsCtrl', ['$scope', '$window', '$state', '$modal', '$location', '$q', 'api', 'zemUserSettings', '$timeout', 'zemFilterService', 'zemPostclickMetricsService', 'zemOptimisationMetricsService', function ($scope, $window, $state, $modal, $location, $q, api, zemUserSettings, $timeout, zemFilterService, zemPostclickMetricsService, zemOptimisationMetricsService) { // eslint-disable-line max-len
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
    $scope.localStoragePrefix = 'adGroupContentAds';
    $scope.infoboxLinkTo = 'main.adGroups.settings';

    $scope.lastSyncDate = null;
    $scope.isSyncRecent = true;
    $scope.isSyncInProgress = false;
    $scope.selectionMenuConfig = {};

    // selection triplet - all, a batch, or specific content ads can be selected
    $scope.selectedAll = false;
    $scope.selectedBatchId = null;
    $scope.selectedContentAdsStatus = {};

    $scope.archivingResults = null;
    $scope.closeArchivingResults = function () {
        $scope.archivingResults = null;
    };

    $scope.pagination = {
        currentPage: 1
    };

    $scope.exportOptions = [
      {name: 'By Ad Group (totals)', value: constants.exportType.AD_GROUP},
      {name: 'Current View', value: constants.exportType.CONTENT_AD, defaultOption: true},
    ];

    $scope.bulkActions = [{
        name: 'Pause',
        value: 'pause',
        hasPermission: true,
    }, {
        name: 'Resume',
        value: 'resume',
        hasPermission: true
    }, {
        name: 'Download',
        value: 'download',
        hasPermission: true,
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

    $scope.selectedAdsChanged = function (row, checked) {
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

    $scope.updateContentAdSelection = function () {
        $scope.rows.forEach(function (row) {
            if ($scope.selectedContentAdsStatus[row.id] !== undefined) {
                row.ad_selected = $scope.selectedContentAdsStatus[row.id];
            } else if ($scope.selectedAll) {
                row.ad_selected = true;
            } else if ($scope.selectedBatchId && row.batch_id === $scope.selectedBatchId) {
                row.ad_selected = true;
            } else {
                row.ad_selected = false;
            }
        });
    };

    $scope.isAnythingSelected = function () {
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
        shown: true,
        hasPermission: true,
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
        internal: false,
        shown: true,
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
        getDisabledMessage: function (row) {
            return 'This ad must be managed manually.';
        },
        disabled: false,
        archivedField: 'archived'
    }, {
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
        shown: $scope.hasPermission('zemauth.campaign_goal_performance')
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
        help: 'The amount spent per content ad.',
        totalRow: true,
        order: true,
        initialOrder: 'desc',
        shown: !$scope.hasPermission('zemauth.can_view_effective_costs') && !$scope.hasPermission('zemauth.can_view_actual_costs')
    }, {
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
    }, {
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
    }, {
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
    }, {
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
    }, {
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
    }, {
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
    }, {
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
        'name': 'Costs',
        'fields': ['cost', 'data_cost', 'media_cost', 'e_media_cost', 'e_data_cost',
                   'billing_cost', 'license_fee'],
    }, {
        'name': 'Content Sync',
        'fields': ['ad_selected', 'image_urls', 'titleLink', 'urlLink', 'submission_status', 'checked', 'upload_time', 'batch_name', 'display_url', 'brand_name', 'description', 'call_to_action']
    }, {
        'name': 'Traffic Acquisition',
        'fields': ['cpc', 'clicks', 'impressions', 'ctr']
    }, {
        'name': 'Audience Metrics',
        'fields': ['percent_new_users', 'bounce_rate', 'pv_per_visit', 'avg_tos', 'visits', 'pageviews', 'click_discrepancy']
    }, {
        name: 'Conversions',
        fields: ['conversion_goal_1', 'conversion_goal_2', 'conversion_goal_3', 'conversion_goal_4', 'conversion_goal_5']
    }, zemOptimisationMetricsService.createColumnCategories(),
    ];

    $scope.addContentAds = function () {
        var modalInstance = $modal.open({
            templateUrl: '/partials/upload_ads_modal.html',
            controller: 'UploadAdsModalCtrl',
            windowClass: 'modal',
            scope: $scope
        });

        modalInstance.result.then(function () {
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

    $scope.updateTableAfterArchiving = function (data) {
        // update rows immediately, refresh whole table after
        updateTableData(data.data.rows, {});

        if (!isNaN(data.data.archived_count) && !isNaN(data.data.active_count)) {
            $scope.archivingResults = {
                archived_count: data.data.archived_count,
                active_count: data.data.active_count
            };
        } else {
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

    $scope.loadPage = function (page) {
        if (page && page > 0 && page <= $scope.pagination.numPages) {
            $scope.pagination.currentPage = page;
        }

        if ($scope.pagination.currentPage && $scope.pagination.size) {
            $location.search('page', $scope.pagination.currentPage);
            $scope.setAdGroupData('page', $scope.pagination.currentPage);

            getTableData();
        }
    };

    $scope.$watch('size', function (newValue, oldValue) {
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
    });

    $scope.$watch('isSyncInProgress', function (newValue, oldValue) {
        if (newValue === true && oldValue === false) {
            pollSyncStatus();
        }
    });

    var hasMetricData = function (metric) {
        var hasData = false;
        $scope.chartData.groups.forEach(function (group) {
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

    $scope.orderTableData = function (order) {
        $scope.order = order;

        $location.search('order', $scope.order);
        getTableData();
    };

    $scope.toggleChart = function () {
        $scope.chartHidden = !$scope.chartHidden;

        $timeout(function () {
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

    $scope.$watch(zemFilterService.getShowArchived, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }
        getTableData();
        getDailyStats();
    }, true);

    $scope.triggerSync = function () {
        $scope.isSyncInProgress = true;
        api.adGroupSync.get($state.params.id);
    };

    var getTableData = function () {
        $scope.loadRequestInProgress = true;

        api.adGroupAdsTable.get($state.params.id, $scope.pagination.currentPage, $scope.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                var defaultChartMetrics;

                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.order = data.order;
                $scope.pagination = data.pagination;
                $scope.notifications = data.notifications;
                $scope.campaignGoals = data.campaign_goals;
                $scope.lastChange = data.lastChange;

                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;
                $scope.dataStatus = data.dataStatus;

                $scope.pollTableUpdates();
                $scope.updateContentAdSelection();

                zemOptimisationMetricsService.updateVisibility($scope.columns, $scope.campaignGoals);
                zemOptimisationMetricsService.updateChartOptionsVisibility($scope.chartMetricOptions, $scope.campaignGoals);

                $scope.isIncompletePostclickMetrics = data.incomplete_postclick_metrics;
                zemPostclickMetricsService.setConversionGoalColumnsDefaults($scope.columns, data.conversionGoals);

                initUploadBatches(data.batches);
                contentAdsNotLoaded.resolve($scope.rows.length === 0);
                // when switching windows between campaigns with campaign goals defined and campaigns without campaign goals defined
                // make sure chart selection gets updated
                defaultChartMetrics = $scope.defaultChartMetrics($scope.chartMetric1, $scope.chartMetric2, $scope.chartMetricOptions);
                $scope.chartMetric1 = defaultChartMetrics.metric1 || $scope.chartMetric1;
                $scope.chartMetric2 = defaultChartMetrics.metric2 || $scope.chartMetric2;
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
            }, 10000);
        }
    };

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
            true,
            false
        );

        zemPostclickMetricsService.insertConversionGoalColumns(
            $scope.columns,
            $scope.columns.length - 1,
            true,
            false
        );

        zemOptimisationMetricsService.insertAudienceOptimizationColumns(
            $scope.columns,
            $scope.columns.length - 1,
            $scope.hasPermission('zemauth.campaign_goal_optimization'),
            $scope.isPermissionInternal('zemauth.campaign_goal_optimization')
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
        getInfoboxData();

        initColumns();

        pollSyncStatus();
    };

    $scope.pollTableUpdates = function () {
        if ($scope.lastChangeTimeout) {
            return;
        }

        api.adGroupAdsTable.getUpdates($state.params.id, $scope.lastChange)
            .then(function (data) {
                if (data.lastChange) {
                    $scope.lastChange = data.lastChange;
                    $scope.notifications = data.notifications;

                    $scope.updateDataStatus(data.dataStatus);
                    updateTableData(data.rows, data.totals);
                }

                if (data.inProgress) {
                    $scope.lastChangeTimeout = $timeout(function () {
                        $scope.lastChangeTimeout = null;
                        $scope.pollTableUpdates();
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

    $scope.updateDataStatus = function (newDataStatus) {
        for (var rowid in newDataStatus) {
            var newStatus = newDataStatus[rowid];
            if (newStatus) {
                $scope.dataStatus[rowid] = newStatus;
            }
        }
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


    var getDailyStats = function () {
        api.dailyStats.listContentAdStats($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, getDailyStatsMetrics()).then(
            function (data) {
                setChartOptions(data.goals);
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
        api.adGroupOverview.get(
            $state.params.id,
            $scope.dateRange.startDate,
            $scope.dateRange.endDate).then(
            function (data) {
                $scope.setInfoboxHeader(data.header);
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
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

        $scope.chartMetricOptions = zemPostclickMetricsService.concatEngagementChartOptions(
            $scope.chartMetricOptions,
            false
        );

        $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
            $scope.chartMetricOptions,
            options.adGroupConversionGoalChartMetrics,
            false
        );

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

        if ($scope.hasPermission('zemauth.campaign_goal_optimization')) {
            $scope.chartMetricOptions = zemOptimisationMetricsService.concatChartOptions(
                $scope.campaignGoals,
                $scope.chartMetricOptions,
                options.campaignGoalChartMetrics.concat(options.campaignGoalConversionGoalChartMetrics),
                $scope.isPermissionInternal('zemauth.campaign_goal_optimization')
            );
        }
    };

    var setConversionGoalChartOptions = function (conversionGoals) {
        var validChartMetrics = zemPostclickMetricsService.getValidChartMetrics($scope.chartMetric1, $scope.chartMetric2, conversionGoals);
        $scope.chartMetric1 = validChartMetrics.chartMetric1;
        $scope.chartMetric2 = validChartMetrics.chartMetric2;
        zemPostclickMetricsService.setConversionGoalChartOptions(
            $scope.chartMetricOptions,
            conversionGoals
        );
    };

    init();
}]);
