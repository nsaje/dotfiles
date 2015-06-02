/* globals oneApp, options */
oneApp.controller('AdGroupAdsPlusCtrl', ['$scope', '$window', '$state', '$modal', '$location', 'api', 'zemUserSettings', 'zemCustomTableColsService', '$timeout', 'zemFilterService', function ($scope, $window, $state, $modal, $location, api, zemUserSettings, zemCustomTableColsService, $timeout, zemFilterService) {
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

	// selectiont triple - all, a batch, or specific content ad's can be selected
	$scope.selectedAll = false;
	$scope.selectedBatches = [];
	$scope.selectedContentAdsStatus = {};

    $scope.pagination = {
        currentPage: 1
    };

    $scope.exportOptions = [
        {name: 'CSV by day', value: 'csv'},
        {name: 'Excel by day', value: 'excel'}
    ];

    $scope.selectedAdsChanged = function (row, checked) {
        if (row.id) {
        	$scope.selectedContentAdsStatus[row.id] = checked;
        }  
    };

	$scope.logSelection = function () {
		/*
		// selection triple - all, a batch, or specific content ad's can be selected
		console.log($scope.selectedAll);
		console.log($scope.selectedBatches);
		console.log($scope.selectedContentAdsStatus);
		*/
	};

    $scope.selectAllCallback = function (ev) {
		// selection triple - all, a batch, or specific content ad's can be selected
		$scope.selectedAll = true;
		$scope.selectedBatches = [];
		$scope.selectedContentAdsStatus = {};

		$scope.updateContentAdSelection();
		$scope.logSelection();
	};

    $scope.selectThisPageCallback = function (ev) {
		// selection triple - all, a batch, or specific content ad's can be selected
		$scope.selectedAll = false;
		$scope.selectedBatches = [];
		$scope.selectedContentAdsStatus = {};

		$scope.rows.forEach(function (row) {
			$scope.selectedContentAdsStatus[row.id] = true;
		});

		$scope.updateContentAdSelection();
		$scope.logSelection();
	};

    $scope.selectBatchCallback = function (name) {
		// selection triple - all, a batch, or specific content ad's can be selected
		$scope.selectedAll = false;
		$scope.selectedBatches = [name];
		$scope.selectedContentAdsStatus = {};
		
		$scope.updateContentAdSelection();
		$scope.logSelection();
	};

	$scope.updateContentAdSelection = function () {
		$scope.rows.forEach(function (row) {
			if ($scope.selectedContentAdsStatus[row.id] !== undefined) {
				row.ad_selected = $scope.selectedContentAdsStatus[row.id];
			} else if ($scope.selectedAll) {
				row.ad_selected = true;
			} else if (($scope.selectedBatches.length > 0) && 
					   (row.batch_name == $scope.selectedBatches[0])) { 
				row.ad_selected = true;
			} else {
				row.ad_selected = false;
			}
		});

	};

	$scope.selectionOptionsStatic = [
		{
			name: 'All',
			type: 'link',
			callback: $scope.selectAllCallback
		}, {
			name: 'This page',
			type: 'link',
			callback: $scope.selectThisPageCallback
		}, {
			type: 'separator'
		}
	];

    $scope.selectionOptions = $scope.selectionOptionsStatic.concat([{
			title: 'Upload batch',
			name: '',
			type: 'link-list-item-first',
		}
    ]);

    $scope.columns = [
		{
			name: 'zem-simple-menu',
			field: 'ad_selected',
			type: 'checkbox',
			shown: $scope.hasPermission('zemauth.content_ads_bulk_actions'),
			hasPermission: $scope.hasPermission('zemauth.content_ads_bulk_actions'),
			checked: true,
			totalRow: true,
			unselectable: true,
			order: false,
			selectCallback: $scope.selectedAdsChanged,
			disabled: false,
			selectionOptions: $scope.selectionOptions
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
            onChange: function (sourceId, state) {
                api.adGroupContentAdState.save($state.params.id, [sourceId], state).then(
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
            checked: false,
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
        }
    ];    
	// 'urlLink1', 'urlLink', 
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

        modalInstance.result.then(function () {
            getTableData();
        });

        return modalInstance;
    };

    $scope.bulkEdit = function() {
		if ($scope.selectedBulkAction == null) {
			return;
		}
    	// TODO: replace ad lookups with selection buffer lookups
		var content_ad_ids_true = [],
			content_ad_ids_false = [];

		// $scope.selectedAll = false;
		// $scope.selectedBatches = [];
		// $scope.selectedContentAdsStatus = {};

		for (var selectedContentAd in $scope.selectedContentAdsStatus) {
			if ($scope.selectedContentAdsStatus[selectedContentAd]) {
				content_ad_ids_true.push(selectedContentAd);
			} else {
				content_ad_ids_false.push(selectedContentAd);
			}
		}

		if ($scope.selectedBulkAction == 'pause') {
            api.adGroupContentAdState.save(
            		$state.params.id, 
            		content_ad_ids_true, 
            		content_ad_ids_false,
            		$scope.selectedAll,
            		$scope.selectedBatches,
            		constants.contentAdSourceState.INACTIVE).then(
                function () {
                    pollTableUpdates();
                }
            );
		} else if ($scope.selectedBulkAction == 'resume') {
            api.adGroupContentAdState.save(
            		$state.params.id, 
            		content_ad_ids_true, 
            		content_ad_ids_false,
            		$scope.selectedAll,
            		$scope.selectedBatches,
            		constants.contentAdSourceState.ACTIVE).then(
                function () {
                    pollTableUpdates();
                }
            );
		} else if ($scope.selectedBulkAction == 'download') {
            var url = '/api/ad_groups/' + $state.params.id + 
            	'/contentads/csv/?content_ad_ids_enabled=' + content_ad_ids_true.join(',') +
            	'&content_ad_ids_disabled=' + content_ad_ids_false.join(',');
			url += '&select_all=' + $scope.selectedAll;
			if ($scope.selectedBatches.length > 0) {
				url += '&select_batch=' + $scope.selectedBatches[0];
			}
			
            $window.open(url, '_blank');            
		} else {
			// TODO: Signal error
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

    var initSelectionOptions = function () {
        var options;
        cols = zemCustomTableColsService.load('adGroupAdsPlus', $scope.columns);
        $scope.selectedColumnsCount = cols.length;
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

	var initUploadBatches = function () {
		// refresh upload batches for current adgroup
		api.adGroupAdsPlusUploadBatches.list($state.params.id).then(function(data) {
			var dataEntry = data['data']['batches'],
				entries = [];

 	        dataEntry.forEach(function (entry) {
 	        	entry['callback'] = $scope.selectBatchCallback;
				entry['type'] = 'link-list-item';
 	        	entries.push(entry);
			});

			if (entries.length > 0) {
				entries[0]['type'] = 'link-list-item-first';
			}

			var i = 0;
			$scope.columns.forEach(function(col) {
				if (col.name == 'zem-simple-menu') {
					$scope.columns[i].selectionOptions = $scope.selectionOptionsStatic.concat(entries);
				}
				i += 1;
			});
		});
	};


    var init = function() {
        if (!$scope.adGroup.contentAdsTabWithCMS && !$scope.hasPermission('zemauth.new_content_ads_tab')) {
            $state.go('main.adGroups.ads', {id: $scope.adGroup.id});
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
