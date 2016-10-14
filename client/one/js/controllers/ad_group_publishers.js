/*globals angular,moment,constants,options*/

angular.module('one.legacy').controller('AdGroupPublishersCtrl', ['$scope', '$state', '$location', '$timeout', '$window', 'api', 'zemPostclickMetricsService', 'zemFilterService', 'zemUserSettings', 'zemDataFilterService', function ($scope, $state, $location, $timeout, $window, api, zemPostclickMetricsService, zemFilterService, zemUserSettings, zemDataFilterService) {
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
    $scope.order = '-media_cost';
    $scope.localStoragePrefix = 'adGroupPublishers';
    $scope.page = {
        sizeRange: [5, 10, 20, 50],
        size: 5
    };
    $scope.size = $scope.page.size;
    $scope.rows = [];
    $scope.isSyncInProgress = false;
    $scope.infoboxLinkTo = 'main.adGroups.settings';
    $scope.pagination = {
        currentPage: 1
    };
    $scope.obBlacklistedCount = 0;
    $scope.obBlacklistedSelected = 0;

    $scope.grid = {
        api: undefined,
        level: constants.level.AD_GROUPS,
        breakdown: constants.breakdown.PUBLISHER,
        entityId: $state.params.id,
    };

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

        $scope.updatePublisherBlacklistCombo();

        if ($scope.selectedAll) {
            $scope.selectionMenuConfig.partialSelection = numNotSelected > 0;
        }
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
            $scope.updateRowBlacklistInfo();
        } else {
            $scope.clearPublisherSelection();
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
        internal: $scope.isPermissionInternal('zemauth.can_view_platform_cost_breakdown'),
        shown: $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
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
        internal: $scope.isPermissionInternal('zemauth.can_view_platform_cost_breakdown'),
        shown: $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
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
        internal: $scope.isPermissionInternal('zemauth.can_view_platform_cost_breakdown'),
        shown: $scope.hasPermission('zemauth.can_view_platform_cost_breakdown')
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
        internal: false,
        shown: true,
    },
    {
        name: 'Margin',
        field: 'margin',
        checked: false,
        type: 'currency',
        totalRow: true,
        help: 'Agency\'s margin',
        order: true,
        initialOrder: 'desc',
        internal: $scope.isPermissionInternal('zemauth.can_view_agency_margin'),
        shown: $scope.hasPermission('zemauth.can_view_agency_margin')
    },
    {
        name: 'Total Spend + Margin',
        field: 'agency_total',
        checked: false,
        type: 'currency',
        totalRow: true,
        help: 'Total billing cost including Media Spend, License Fee and Agency Margin',
        order: true,
        initialOrder: 'desc',
        internal: $scope.isPermissionInternal('zemauth.can_view_agency_margin'),
        shown: $scope.hasPermission('zemauth.can_view_agency_margin')
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
        name: 'Avg. CPM',
        field: 'cpm',
        checked: true,
        type: 'currency',
        fractionSize: 3,
        help: 'Cost per 1,000 impressions',
        totalRow: true,
        order: true,
        initialOrder: 'desc',
        shown: true,
        internal: false,
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
                'cpc',
                'cpm',
                'clicks',
                'impressions',
                'ctr',
                'media_cost',
                'data_cost',
                'e_media_cost',
                'e_data_cost',
                'billing_cost',
                'license_fee',
                'margin',
                'agency_total',
            ]
        },
        {
            'name': 'Audience Metrics',
            'fields': [
                'visits', 'pageviews', 'percent_new_users',
                'bounce_rate', 'pv_per_visit', 'avg_tos',
                'click_discrepancy', 'unique_users', 'new_users', 'returning_users',
                'bounced_visits', 'non_bounced_visits', 'total_seconds']
        },
        {
            'name': 'Conversions',
            'fields': ['conversion_goals_placeholder', 'pixels_placeholder'],
        }, {
            'name': 'Goals',
            'fields': ['avg_cost_per_visit', 'avg_cost_for_new_visitor', 'avg_cost_per_pageview',
                       'avg_cost_per_non_bounced_visit', 'avg_cost_per_minute', 'conversion_goals_avg_cost_placeholder',
                       'pixels_avg_cost_placeholder'],
        }];

    $scope.initColumns = function () {
        zemPostclickMetricsService.insertAcquisitionColumns(
            $scope.columns,
            $scope.columns.length,
            $scope.hasPermission('zemauth.view_pubs_postclick_acquisition'),
            $scope.isPermissionInternal('zemauth.view_pubs_postclick_acquisition')
        );

        zemPostclickMetricsService.insertEngagementColumns(
            $scope.columns,
            $scope.columns.length,
            true,
            false
        );

        zemPostclickMetricsService.insertConversionsPlaceholders(
            $scope.columns,
            $scope.columns.length - 2
        );

        zemPostclickMetricsService.insertAudienceOptimizationColumns(
            $scope.columns,
            $scope.columns.length
        );

        zemPostclickMetricsService.insertCPAPlaceholders(
            $scope.columns,
            $scope.columns.length - 2
        );
    };

    $scope.loadRequestInProgress = false;

    $scope.orderTableData = function (order) {
        $scope.order = order;
        getTableData();
    };


    var bulkUpdatePublishers = function (publishersSelected, publishersNotSelected, state, level) {
        var dateRange = zemDataFilterService.getDateRange();
        api.adGroupPublishersState.save(
            $state.params.id,
            state,
            level,
            dateRange.startDate,
            dateRange.endDate,
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

        var dateRange = zemDataFilterService.getDateRange();
        api.adGroupPublishersTable.get($state.params.id, $scope.pagination.currentPage, $scope.page.size, dateRange.startDate, dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.totals.checked = $scope.selectedTotals;
                $scope.lastChange = data.lastChange;
                $scope.pagination = data.pagination;
                $scope.obBlacklistedCount = data.obBlacklistedCount;
                $scope.campaignGoals = data.campaign_goals;

                $scope.updatePublisherSelection();
                $scope.updateRowBlacklistInfo();

                zemPostclickMetricsService.insertConversionGoalColumns($scope.columns, $scope.columnCategories, data.conversionGoals);
                zemPostclickMetricsService.insertPixelColumns($scope.columns, $scope.columnCategories, data.pixels);
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
        // always query for default metrics
        var metrics = [$scope.chartMetric1, $scope.chartMetric2];
        if (metrics.indexOf(constants.chartMetric.CLICKS) < 0) {
            metrics.push(constants.chartMetric.CLICKS);
        }
        if (metrics.indexOf(constants.chartMetric.IMPRESSIONS) < 0) {
            metrics.push(constants.chartMetric.IMPRESSIONS);
        }
        return metrics;
    };

    var refreshChartOptions = function (conversionGoals, pixels) {
        zemPostclickMetricsService.insertConversionsGoalChartOptions($scope.chartMetricOptions, conversionGoals);
        zemPostclickMetricsService.insertPixelChartOptions($scope.chartMetricOptions, pixels);

        var validChartMetrics = zemPostclickMetricsService.getValidChartMetrics($scope.chartMetric1, $scope.chartMetric2, $scope.chartMetricOptions);
        if ($scope.chartMetric1 !== validChartMetrics.metric1) $scope.chartMetric1 = validChartMetrics.metric1;
        if ($scope.chartMetric2 !== validChartMetrics.metric2) $scope.chartMetric2 = validChartMetrics.metric2;
    };

    var setChartOptions = function (goals) {
        $scope.chartMetricOptions = options.adGroupChartMetrics;

        if ($scope.hasPermission('zemauth.view_pubs_postclick_acquisition')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatAcquisitionChartOptions(
                $scope.chartMetricOptions,
                $scope.isPermissionInternal('zemauth.view_pubs_postclick_acquisition')
            );
        }

        $scope.chartMetricOptions = zemPostclickMetricsService.concatEngagementChartOptions(
            $scope.chartMetricOptions,
            false
        );

        if ($scope.hasPermission('zemauth.can_view_platform_cost_breakdown')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                options.platformCostChartMetrics,
                $scope.isPermissionInternal('zemauth.can_view_platform_cost_breakdown')
            );
        }

        $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
            $scope.chartMetricOptions,
            options.billingCostChartMetrics,
            false
        );

        if ($scope.hasPermission('zemauth.can_view_actual_costs')) {
            $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
                $scope.chartMetricOptions,
                options.actualCostChartMetrics,
                $scope.isPermissionInternal('zemauth.can_view_actual_costs')
            );
        }

        $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
            $scope.chartMetricOptions,
            options.conversionChartMetrics
        );

        $scope.chartMetricOptions = zemPostclickMetricsService.concatChartOptions(
            $scope.chartMetricOptions,
            options.goalChartMetrics
        );
    };

    var getDailyStats = function () {
        $scope.selectedPublisherIds = [];
        $scope.selectedTotals = true;

        var dateRange = zemDataFilterService.getDateRange();
        api.dailyStats.listPublishersStats($state.params.id, dateRange.startDate, dateRange.endDate, $scope.selectedPublisherIds,  $scope.selectedTotals, getDailyStatsMetrics()).then(
            function (data) {
                refreshChartOptions(data.conversionGoals, data.pixels);

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
        var dateRange = zemDataFilterService.getDateRange();
        api.adGroupOverview.get(
            $state.params.id,
            dateRange.startDate,
            dateRange.endDate).then(
            function (data) {
                $scope.setInfoboxHeader(data.header);
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

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!$scope.isMetricInChartData(newValue, $scope.chartData)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            if (!$scope.isMetricInChartData(newValue, $scope.chartData)) {
                getDailyStats();
            } else {
                // create a copy to trigger watch
                $scope.chartData = angular.copy($scope.chartData);
            }
        }
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

        if (size !== 0 && $scope.page.size !== size) {
            $scope.page.size = size;
        }
        // if nothing in local storage or page query var set first as default
        if ($scope.page.size === 0) {
            $scope.page.size = $scope.page.sizeRange[0];
        }

        setChartOptions();

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
            $scope.setAdGroupData('page', page);
            $location.search('page', page);
        }

        $scope.initColumns();

        $scope.loadPage();

        getTableData();
        getDailyStats();
        $scope.getInfoboxData();
        zemFilterService.setShowBlacklistedPublishers(true);

        var dateRangeUpdateHandler = zemDataFilterService.onDateRangeUpdate(function () {
            getTableData();
            getDailyStats();
        });
        $scope.$on('$destroy', dateRangeUpdateHandler);

        $scope.setActiveTab();
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

    $scope.$watch('page.size', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.size = $scope.page.size;
            $scope.loadPage();
        }
    });

    $scope.$on('$destroy', function () {
        zemFilterService.setShowBlacklistedPublishers(false);
        $timeout.cancel($scope.lastChangeTimeout);
    });

    $scope.init();
}]);
