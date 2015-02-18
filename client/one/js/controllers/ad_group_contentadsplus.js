/* globals oneApp */
oneApp.controller('AdGroupAdsPlusCtrl', ['$scope', '$state', '$modal', '$location', 'api', 'zemUserSettings', 'zemCustomTableColsService', function ($scope, $state, $modal, $location, api, zemUserSettings, zemCustomTableColsService) {
    $scope.order = '-upload_time';
    $scope.loadRequestInProgress = false;
    $scope.selectedColumnsCount = 0;
    $scope.sizeRange = [5, 10, 20, 50];
    $scope.size = $scope.sizeRange[0];

    $scope.pagination = {
        currentPage: 1
    };

    $scope.columns = [
        {
            name: 'Title',
            field: 'title_link',
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
        }, {
            name: 'URL',
            field: 'url_link',
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
            name: 'Upload Time (EST)',
            field: 'upload_time',
            checked: false,
            type: 'datetime',
            shown: true,
            help: 'The time when the content ad was uploaded.',
            totalRow: false,
            order: true,
            initialOrder: 'desc'
        }, {
            name: 'Upload Batch Name',
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

        return modalInstance;
    };

    $scope.loadPage = function(page) {
        if(page && page > 0 && page <= $scope.pagination.numPages) {
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
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

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

        $scope.loadPage();
        getTableData();
        initColumns();
    };

    init();
}]);
