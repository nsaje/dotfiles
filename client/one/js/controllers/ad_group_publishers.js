/*globals oneApp,moment,constants,options*/

oneApp.controller('AdGroupPublishersCtrl', ['$scope', '$state', '$location', '$timeout', '$window', 'api', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', function ($scope, $state, $location, $timeout, $window, api, zemPostclickMetricsService, zemFilterService, zemUserSettings) {
    $scope.selectedTotals = true;
    $scope.selectedColumnsCount = 0;
    $scope.constants = constants;
    $scope.chartMetric1 = constants.chartMetric.CLICKS;
    $scope.chartMetric2 = constants.chartMetric.IMPRESSIONS;
    $scope.chartData = undefined;
    $scope.chartHidden = false;
    $scope.chartMetricOptions = [];
    $scope.chartGoalMetrics = null;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.order = '-cost';
    $scope.localStoragePrefix = 'adGroupPublishers';
    $scope.sizeRange = [5, 10, 20, 50];
    $scope.size = $scope.sizeRange[0];
    $scope.rows = [];
    $scope.isSyncInProgress = false;
    $scope.infoboxLinkTo = 'main.adGroups.settings';
    $scope.pagination = {
        currentPage: 1
    };
    $scope.obBlacklistedCount = 0;
    $scope.obBlacklistedSelected = 0;

    var userSettings = zemUserSettings.getInstance($scope, $scope.localStoragePrefix);

    $scope.selectionMenuConfig = {
        hideCombo: true
    };
    // selection settings - all or specific publishers can be selected
    $scope.selectedAll = false;
    $scope.selectedPublisherStatus = {};

    $scope.bulkBlacklistActions = [{
        name: 'Blacklist in this adgroup',
        value: 'blacklist-adgroup',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status')
    }, {
        name: 'Blacklist in this campaign',
        value: 'blacklist-campaign',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Blacklist in this account',
        value: 'blacklist-account',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Blacklist globally',
        value: 'blacklist-global',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_global_publisher_blacklist_status')
    }];

    $scope.bulkEnableActions = [{
        name: 'Re-enable in this adgroup',
        value: 'enable-adgroup',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status')
    }, {
        name: 'Re-enable in this campaign',
        value: 'enable-campaign',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Re-enable in this account',
        value: 'enable-account',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_campaign_account_publisher_blacklist_status')
    }, {
        name: 'Re-enable globally',
        value: 'enable-global',
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status') &&
            $scope.hasPermission('zemauth.can_access_global_publisher_blacklist_status')
    }];

    $scope.calculatePublisherHash = function (row) {
        // very simplistic hash to allow blacklist selection
        return row.exchange + ' ' + row.domain;
    };

    $scope.setAllBulkAction = function (action, enabled) {
        $scope.setBulkAction(null, action, enabled);
    };

    $scope.setBulkAction = function (level, action, enabled) {
        var postfix = level || '.*',
            matchRegex = new RegExp('^'.concat(action, '-', postfix, '$'));

        $scope.bulkBlacklistActions.forEach(function (bulkAction) {
            if (matchRegex.test(bulkAction.value)) {
                bulkAction.disabled = !enabled;
            }
        });
        $scope.bulkEnableActions.forEach(function (bulkAction) {
            if (matchRegex.test(bulkAction.value)) {
                bulkAction.disabled = !enabled;
            }
        });
    };

    $scope.selectedPublisherChanged = function (row, checked) {
        var numNotSelected = 0;

        $scope.selectedPublisherStatus[$scope.calculatePublisherHash(row)] = {
            'checked': checked,
            'source_id': row.source_id,
            'domain': row.domain,
            'exchange': row.exchange,
            'external_id': row.external_id,
            'blacklisted': row.blacklisted,
            'blacklisted_level': row.blacklisted_level
        };

        Object.keys($scope.selectedPublisherStatus).forEach(function (publisherId) {
            var pubStatus = $scope.selectedPublisherStatus[publisherId];
            if (!pubStatus.checked) {
                numNotSelected += 1;
            }
        });
        $scope.recountOutbrainPublishers();

        $scope.updatePublisherBlacklistCombo();

        if ($scope.selectedAll) {
            $scope.selectionMenuConfig.partialSelection = numNotSelected > 0;
        }

        if (row.exchange === constants.sourceTypeName.OUTBRAIN) {
            $scope.updateOutbrainPublisherSelection();
            $scope.updateRowBlacklistInfo();
        }
    };

    $scope.recountOutbrainPublishers = function () {
        $scope.obBlacklistedSelected = 0;
        Object.keys($scope.selectedPublisherStatus).forEach(function (publisherId) {
            var pubStatus = $scope.selectedPublisherStatus[publisherId];
            if (pubStatus.exchange === constants.sourceTypeName.OUTBRAIN && pubStatus.checked && pubStatus.blacklisted !== 'Blacklisted') {
                $scope.obBlacklistedSelected += 1;
            }
        });
    };

    $scope.updatePublisherBlacklistCombo = function () {
        var count = {},
            levels = [
                constants.publisherBlacklistLevel.ADGROUP,
                constants.publisherBlacklistLevel.CAMPAIGN,
                constants.publisherBlacklistLevel.ACCOUNT,
                constants.publisherBlacklistLevel.GLOBAL
            ];

        count.countBlacklistedSelected = 0;
        count.countNonBlacklistedSelected = 0;
        count.countOutbrainSelected = 0;
        count.countAllSelected = 0;
        count.maxBlacklistedLevel = null;

        Object.keys($scope.selectedPublisherStatus).forEach(function (key) {
            var entry = $scope.selectedPublisherStatus[key];
            if (entry.checked) {
                count = $scope.countPublisherBlacklistEntry(count, entry);
            }
        });

        if ($scope.selectedAll) {
            $scope.rows.forEach(function (row) {
                count = $scope.countPublisherBlacklistEntry(count, row);
            });
        }

        count.countAllSelected = count.countBlacklistedSelected + count.countNonBlacklistedSelected;
        if (count.maxBlacklistedLevel !== null) {
            if (count.countBlacklistedSelected > 0 || $scope.selectedAll) {
                levels.forEach(function (level) {
                    // user can only enable blacklist on currently
                    // blacklisted level
                    var enabled = $scope.levelEq(level, count.maxBlacklistedLevel);
                    $scope.setBulkAction(level, 'enable', enabled);

                    var blacklistedEnabled = $scope.levelGt(level, count.maxBlacklistedLevel);
                    // user can always blacklist on higher level
                    // than currently blacklisted
                    $scope.setBulkAction(level, 'blacklist', blacklistedEnabled);
                });
            }
        }

        if (count.countNonBlacklistedSelected > 0) {
            levels.forEach(function (level) {
                var enabled = $scope.levelGt(level, count.maxBlacklistedLevel);
                // user can always blacklist on higher level
                // than currently blacklisted
                $scope.setBulkAction(level, 'blacklist', enabled);
            });
        }

        if (count.countOutbrainSelected > 0) {
            // user can always blacklist on higher level
            // than currently blacklisted
            var disabledOutbrainLevels = [
                constants.publisherBlacklistLevel.ADGROUP,
                constants.publisherBlacklistLevel.CAMPAIGN,
                constants.publisherBlacklistLevel.GLOBAL
            ];
            disabledOutbrainLevels.forEach(function (level) {
                $scope.setBulkAction(level, 'blacklist', false);
                $scope.setBulkAction(level, 'enable', false);
            });
        }
    };

    $scope.countPublisherBlacklistEntry = function (count, entry) {
        var newCount = angular.copy(count);

        if (entry.blacklisted === 'Blacklisted') {
            newCount.countBlacklistedSelected += 1;
            if (newCount.maxBlacklistedLevel === null || $scope.levelGt(entry.blacklisted_level, newCount.maxBlacklistedLevel)) {
                newCount.maxBlacklistedLevel = entry.blacklisted_level;
            }
        } else if (entry.blacklisted === 'Active') {
            newCount.countNonBlacklistedSelected += 1;
        }
        if (entry.exchange === 'Outbrain') {
            newCount.countOutbrainSelected += 1;
        }

        return newCount;
    };

    $scope.compareLevels = function (level1, level2) {
        var map = { };
        map[constants.publisherBlacklistLevel.ADGROUP] = 1;
        map[constants.publisherBlacklistLevel.CAMPAIGN] = 2;
        map[constants.publisherBlacklistLevel.ACCOUNT] = 3;
        map[constants.publisherBlacklistLevel.GLOBAL] = 4;
        if (map[level1] < map[level2]) {
            return -1;
        }
        if (map[level1] === map[level2]) {
            return 0;
        }
        return 1;
    };

    $scope.levelEq = function (level1, level2) {
        return $scope.compareLevels(level1, level2) === 0;
    };

    $scope.levelGt = function (level1, level2) {
        return $scope.compareLevels(level1, level2) > 0;
    };

    $scope.selectionMenuConfig.selectAllCallback = function (selected) {
        $scope.selectionMenuConfig.partialSelection = false;
        $scope.selectedAll = selected;
        $scope.selectedPublisherStatus = {};

        if (selected) {
            $scope.updatePublisherSelection();
            $scope.updateOutbrainPublisherSelection();
            $scope.updateRowBlacklistInfo();
        } else {
            $scope.clearPublisherSelection();
            $scope.updateOutbrainPublisherSelection();
        }

        $scope.updatePublisherBlacklistCombo();
    };

    $scope.clearPublisherSelection = function () {
        $scope.rows.forEach(function (row) {
            row.publisherSelected = false;
        });

        $scope.obBlacklistedSelected = 0;
    };

    $scope.updatePublisherSelection = function () {
        $scope.rows.forEach(function (row) {
            if (row === undefined) {
                return;
            }
            row.disabledSelection = !row.can_blacklist_publisher;
            if (row.can_blacklist_publisher) {
                var rowId = $scope.calculatePublisherHash(row);
                if ($scope.selectedPublisherStatus[rowId] !== undefined) {
                    row.publisherSelected = $scope.selectedPublisherStatus[rowId].checked;
                } else if ($scope.selectedAll) {
                    row.publisherSelected = true;
                } else {
                    row.publisherSelected = false;
                }
            }
        });
    };

    $scope.updateOutbrainPublisherSelection = function () {
        $scope.rows.forEach(function (row) {
            if (row !== undefined) {
                if (row.exchange === constants.sourceTypeName.OUTBRAIN) {
                    if (!row.publisherSelected && row.blacklisted !== 'Blacklisted') {
                        if ($scope.obBlacklistedCount + $scope.obBlacklistedSelected >= 10) {
                            row.can_blacklist_publisher = false;
                        }
                    }

                    if ($scope.obBlacklistedCount + $scope.obBlacklistedSelected < 10) {
                        row.can_blacklist_publisher = true;
                    }

                    row.disabledSelection = !row.can_blacklist_publisher;
                }
            }
        });
    };

    $scope.updateRowBlacklistInfo = function () {
        $scope.rows.forEach(function (row) {
            if (row !== undefined) {
                if (!row.can_blacklist_publisher) {
                    row.blacklistInfo = 'This publisher can\'t be blacklisted because the media source doesn\'t support publisher blacklisting or the limit of max blacklisted publisher on this particular media source has been reached. ';
                    row.blacklistInfo = row.blacklistInfo.concat('Contact your account manager for further details.');
                } else {
                    row.blacklistInfo = null;
                }
            }
        });
    };

    $scope.isAnythingSelected = function () {
        var publisherId = 0;

        if ($scope.selectedAll) {
            return true;
        }

        for (publisherId in $scope.selectedPublisherStatus) {
            if ($scope.selectedPublisherStatus.hasOwnProperty(publisherId) &&
                    $scope.selectedPublisherStatus[publisherId].checked) {
                return true;
            }
        }

        return false;
    };

    var pollSyncStatus = function () {
        if ($scope.isSyncInProgress) {
            $timeout(function () {
                api.checkPublisherBlacklistSyncProgress.get($state.params.id).then(
                    function (data) {
                        $scope.isSyncInProgress = data.data.is_sync_in_progress;
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

    $scope.triggerSync = function () {
        $scope.isSyncInProgress = true;
    };

    $scope.executeBulkAction = function (composedAction) {
        if (!$scope.isAnythingSelected()) {
            return;
        }

        var publishersSelected = [],
            publishersNotSelected = [],
            splitAction = composedAction.split('-'),
            action = splitAction[0],
            level = splitAction[1],
            state = null;

        if (level === constants.publisherBlacklistLevel.GLOBAL) {
            if (!confirm('This action will affect all accounts. Are you sure you want to proceed?')) {
                return;
            }
        }

        Object.keys($scope.selectedPublisherStatus).forEach(function (publisherId) {
            if ($scope.selectedPublisherStatus[publisherId] !== undefined) {
                if ($scope.selectedPublisherStatus[publisherId].checked) {
                    publishersSelected.push($scope.selectedPublisherStatus[publisherId]);
                } else {
                    publishersNotSelected.push($scope.selectedPublisherStatus[publisherId]);
                }
            }
        });

        if (action === 'enable') {
            state = constants.publisherStatus.ENABLED;
        } else {
            state = constants.publisherStatus.BLACKLISTED;
        }
        bulkUpdatePublishers(publishersSelected, publishersNotSelected, state, level);
    };

    $scope.columns = [{
        name: '',
        field: 'publisherSelected',
        type: 'checkbox',
        showSelectionMenu: true,
        shown: $scope.hasPermission('zemauth.can_see_publisher_blacklist_status'),
        hasPermission: $scope.hasPermission('zemauth.can_modify_publisher_blacklist_status'),
        checked: true,
        totalRow: false,
        unselectable: true,
        order: false,
        popupField: 'blacklistInfo',
        selectCallback: $scope.selectedPublisherChanged,
        disabled: false,
        selectionMenuConfig: $scope.selectionMenuConfig
    },
    {

        name: 'Status',
        field: 'blacklisted',
        checked: true,
        extraTdCss: 'no-wrap',
        type: 'textWithPopup',
        popupField: 'blacklisted_level_description',
        shown: $scope.hasPermission('zemauth.can_see_publisher_blacklist_status'),
        help: 'Blacklisted status of a publisher.',
        totalRow: false,
        order: false,
        initialOrder: 'asc'
    },
    {
        name: 'Domain',
        field: 'domain',
        unselectable: false,
        checked: true,
        type: 'clickPermissionOrText',
        shown: true,
        hasTotalsLabel: true,
        totalRow: false,
        help: 'A publisher where your content is being promoted.',
        order: true,
        initialOrder: 'asc'
    },
    {
        name: 'Link',
        field: 'domain_link',
        unselectable: false,
        checked: true,
        type: 'visibleLink',
        shown: true,
        totalRow: false,
        help: 'Link to a publisher where your content is being promoted.',
        order: false,
        initialOrder: 'asc'
    },
    {
        name: 'Media Source',
        field: 'exchange',
        unselectable: false,
        checked: true,
        type: 'clickPermissionOrText',
        shown: true,
        totalRow: false,
        help: 'An exchange where your content is being promoted.',
        order: true,
        initialOrder: 'asc'
    },
    {
        name: 'Spend',
        field: 'cost',
        checked: true,
        type: 'currency',
        help: 'Amount spent per publisher.',
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
    }
    ];

    $scope.columnCategories = [
        {
            'name': 'Traffic Acquisition',
            'fields': [
                'publisherSelected',
                'blacklisted',
                'domain',
                'domain_link',
                'exchange',
                'cost',
                'cpc',
                'clicks',
                'impressions',
                'ctr',
                'media_cost',
                'data_cost',
                'e_media_cost',
                'e_data_cost',
                'total_cost',
                'billing_cost',
                'license_fee'
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
        }
    ];

    $scope.initColumns = function () {
        zemPostclickMetricsService.insertAcquisitionColumns(
            $scope.columns,
            $scope.columns.length - 1,
            $scope.hasPermission('zemauth.view_pubs_postclick_stats'),
            $scope.isPermissionInternal('zemauth.view_pubs_postclick_stats')
        );

        zemPostclickMetricsService.insertEngagementColumns(
            $scope.columns,
            $scope.columns.length - 1,
            $scope.hasPermission('zemauth.view_pubs_postclick_stats'),
            $scope.isPermissionInternal('zemauth.view_pubs_postclick_stats')
        );
    };

    $scope.loadRequestInProgress = false;

    $scope.orderTableData = function (order) {
        $scope.order = order;
        getTableData();
    };


    var bulkUpdatePublishers = function (publishersSelected, publishersNotSelected, state, level) {
        api.adGroupPublishersState.save(
            $state.params.id,
            state,
            level,
            $scope.dateRange.startDate,
            $scope.dateRange.endDate,
            publishersSelected,
            publishersNotSelected,
            $scope.selectedAll
        ).then(function () {
            $scope.triggerSync();

            // clear publisher selection
            $scope.selectionMenuConfig.partialSelection = false;
            $scope.selectedAll = false;
            $scope.selectedPublisherStatus = {};
            $scope.clearPublisherSelection();
        });
    };


    var getTableData = function (showWaiting) {
        $scope.loadRequestInProgress = true;

        api.adGroupPublishersTable.get($state.params.id, $scope.pagination.currentPage, $scope.size, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {

                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.totals.checked = $scope.selectedTotals;
                $scope.lastChange = data.lastChange;
                $scope.pagination = data.pagination;
                $scope.obBlacklistedCount = data.obBlacklistedCount;

                $scope.recountOutbrainPublishers();
                $scope.updatePublisherSelection();
                $scope.updateOutbrainPublisherSelection();
                $scope.updateRowBlacklistInfo();
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

    var setChartOptions = function (goals) {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

        if ($scope.hasPermission('zemauth.view_pubs_postclick_stats')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatAcquisitionChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.view_pubs_postclick_stats')
            );
            $scope.chartMetricOptions = zemPostclickMetricsService.concatEngagementChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.view_pubs_postclick_stats')
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

    var getDailyStats = function () {
        $scope.selectedPublisherIds = [];
        $scope.selectedTotals = true;
        api.dailyStats.listPublishersStats($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedPublisherIds,  $scope.selectedTotals, getDailyStatsMetrics()).then(
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

    $scope.getInfoboxData = function () {
        if (!$scope.hasInfoboxPermission()) {
            return;
        }

        api.adGroupOverview.get($state.params.id).then(
            function (data) {
                $scope.infoboxHeader = data.header;
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
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

    // From parent scope (mainCtrl).
    $scope.$watch('dateRange', function (newValue, oldValue) {
        if (newValue.startDate.isSame(oldValue.startDate) && newValue.endDate.isSame(oldValue.endDate)) {
            return;
        }

        getTableData();
        getDailyStats();
    });

    $scope.$watch(zemFilterService.getFilteredSources, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        getTableData();
        getDailyStats();
    }, true);

    $scope.$watch(zemFilterService.getBlacklistedPublishers, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        getTableData();
        getDailyStats();

    }, true);


    $scope.$watch('isSyncInProgress', function (newValue, oldValue) {
        if (newValue === true && oldValue === false) {
            pollSyncStatus();
        }
    }, true);

    $scope.init = function () {
        var data = $scope.adGroupData[$state.params.id];

        var page = parseInt($location.search().page);
        if (isNaN(page)) {
            page = data && data.page;
        }
        var size = parseInt($location.search().size || '0');

        userSettings.registerWithoutWatch('chartMetric1');
        userSettings.registerWithoutWatch('chartMetric2');
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

        $scope.initColumns();

        $scope.loadPage();

        $scope.getAdGroupState();    // To display message if the adgroup is paused

        getTableData();
        getDailyStats();
        $scope.getInfoboxData();
        zemFilterService.setShowBlacklistedPublishers(true);
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

    $scope.$on('$destroy', function () {
        zemFilterService.setShowBlacklistedPublishers(false);
        $timeout.cancel($scope.lastChangeTimeout);
    });

    $scope.init();
}]);
