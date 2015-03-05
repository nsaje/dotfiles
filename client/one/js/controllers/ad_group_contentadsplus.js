/* globals oneApp */
oneApp.controller('AdGroupAdsPlusCtrl', ['$scope', '$state', '$modal', '$location', 'api', 'zemUserSettings', 'zemCustomTableColsService', '$timeout', function ($scope, $state, $modal, $location, api, zemUserSettings, zemCustomTableColsService, $timeout) {
    $scope.order = '-upload_time';
    $scope.loadRequestInProgress = false;
    $scope.selectedColumnsCount = 0;
    $scope.sizeRange = [5, 10, 20, 50];
    $scope.size = $scope.sizeRange[0];
    $scope.lastChangeTimeout = null;

    $scope.pagination = {
        currentPage: 1
    };

    $scope.columns = [
        {
            name: '',
            field: 'image_urls',
            unselectable: true,
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
            unselectable: true,
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
            name: 'Status',
            field: 'submission_status',
            checked: true,
            type: 'submissionStatus',
            shown: true,
            help: 'Current submission status.',
            totalRow: false,
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
            type: 'text',
            shown: true,
            help: 'The name of the upload batch.',
            totalRow: false,
            titleField: 'batch_name',
            order: true,
            orderField: 'batch_name',
            initialOrder: 'asc'
        }
    ];

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

    $scope.orderTableData = function(order) {
        $scope.order = order;

        $location.search('order', $scope.order);
        getTableData();
    };

    var getTableData = function () {
        $scope.loadRequestInProgress = true;

        api.adGroupAdsPlusTable.get($state.params.id, $scope.pagination.currentPage, $scope.size, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.order = data.order;
                $scope.pagination = data.pagination;
                $scope.notifications = data.notifications;
                $scope.lastChange = data.lastChange;

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
        $scope.getAdGroupState();
        initColumns();
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

    init();
}]);
