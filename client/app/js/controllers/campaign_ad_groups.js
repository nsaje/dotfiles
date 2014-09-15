/*globals oneApp,moment,constants*/
oneApp.controller('CampaignAdGroupsCtrl', ['$location', '$scope', '$state', '$timeout', 'api', 'localStorageService', 'zemCustomTableColsService', function ($location, $scope, $state, $timeout, api, localStorageService, zemCustomTableColsService) {
    $scope.getTableDataRequestInProgress = false;
    $scope.addGroupRequestInProgress = false;
    $scope.isSyncInProgress = false;
    $scope.rows = null;
    $scope.totalRow = null;
    $scope.order = '-cost';
    $scope.columns = [
        {
            name: '',
            type: 'checkbox',
            checked: true,
            totalRow: true,
            unselectable: true,
            order: false
        },
        {
            name: 'Name',
            field: 'name',
            unselectable: true,
            checked: true,
            type: 'linkText',
            hasTotalsLabel: true,
            totalRow: false,
            help: 'Name of the ad group.',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'State',
            field: 'state',
            checked: true,
            type: 'text',
            totalRow: false,
            help: 'Status of an ad group (enabled or paused).',
            order: true,
            initialOrder: 'asc'
        },
        {
            name: 'Spend',
            field: 'cost',
            checked: true,
            type: 'currency',
            totalRow: true,
            help: 'The amount spent per ad group.',
            order: true,
            initialOrder: 'desc',
            isDefaultOrder: true
        },
        {
            name: 'Avg. CPC',
            field: 'cpc',
            checked: true,
            type: 'currency',
            fractionSize: 3,
            totalRow: true,
            help: 'The average CPC for each ad group.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number',
            totalRow: true,
            help: 'The number of times ad group\'s content ads have been clicked.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number',
            totalRow: true,
            help: 'The number of times ad group\'s content ads have been displayed.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'CTR',
            field: 'ctr',
            checked: true,
            type: 'percent',
            totalRow: true,
            help: 'The number of clicks divided by the number of impressions.',
            order: true,
            initialOrder: 'desc'
        },
        {
            name: 'Last OK Sync',
            field: 'last_sync',
            checked: false,
            type: 'datetime',
            help: 'Dashboard reporting data is synchronized on an hourly basis. This is when the most recent synchronization occurred.',
            order: true,
            initialOrder: 'desc'
        }
    ];

    $scope.addAdGroup = function () {
        var campaignId = $state.params.id;
        $scope.addGroupRequestInProgress = true;

        api.campaignAdGroups.create(campaignId).then(
            function (data) {
                $scope.accounts.forEach(function (account) {
                    account.campaigns.forEach(function (campaign) {
                        if (campaign.id.toString() === campaignId.toString()) {
                            campaign.adGroups.push({
                                id: data.id,
                                name: data.name
                            });

                            $state.go('main.adGroups.settings', {id: data.id});
                        }
                    });
                });
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.addGroupRequestInProgress = false;
        });
    };

    $scope.getTableData = function () {
        $scope.getTableDataRequestInProgress = true;

        api.campaignAdGroupsTable.get($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.order).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totalRow = data.totals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;
                $scope.isSyncInProgress = data.is_sync_in_progress;

                $scope.order = data.order;

                $scope.rows = $scope.rows.map(function (x) {
                    x.name = {
                        text: x.name,
                        url: $state.href($scope.getDefaultAdGroupState(), {id: x.ad_group})
                    };
                    x.state = x.state === constants.adGroupSettingsState.ACTIVE ? 'Active' : 'Paused';

                    return x;
                });
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.getTableDataRequestInProgress = false;
        });
    };

    $scope.orderTableData = function(order) {
        $scope.order = order;

        $location.search('order', $scope.order);
        localStorageService.set('campaignAdGroups.order', $scope.order);
        $scope.getTableData();
    };

    $scope.triggerSync = function() {
        $scope.isSyncInProgress = true;
        api.campaignSync.get($state.params.id);
    };

    var pollSyncStatus = function() {
        if ($scope.isSyncInProgress){
            $timeout(function() {
                api.checkCampaignSyncProgress.get($state.params.id).then(
                    function(data) {
                        $scope.isSyncInProgress = data.is_sync_in_progress;

                        if (!$scope.isSyncInProgress){
                            // we found out that the sync is no longer in progress
                            // time to reload the data
                            $scope.getTableData();
                            /* $scope.getDailyStats(); */
                        }
                    },
                    function(data) {
                        // error
                        $scope.isSyncInProgress = false;
                    }
                ).finally(function() {
                    pollSyncStatus();
                });
            }, 5000);
        }
    };

    var initColumns = function () {
        var cols;

        cols = zemCustomTableColsService.load('campaignAdGroupsCols', $scope.columns);
        $scope.selectedColumnsCount = cols.length;

        $scope.$watch('columns', function (newValue, oldValue) {
            cols = zemCustomTableColsService.save('campaignAdGroupsCols', newValue);
            $scope.selectedColumnsCount = cols.length;
        }, true);
    };

    $scope.init = function() {
        var order = $location.search().order || localStorageService.get('campaignAdGroups.order') || $scope.order;
        var tableChanged = false;

        if (order !== undefined && $scope.order !== order) {
            $scope.order = order;
            $location.search('order', order);
            tableChanged = true;
        }

        if (tableChanged) {
            $scope.getTableData();
        }

        initColumns();

        pollSyncStatus();
    };

    $scope.$watch('isSyncInProgress', function(newValue, oldValue) {
        if(newValue === true && oldValue === false){
            pollSyncStatus();
        }
    });

    $scope.$watch('dateRange', function (newValue, oldValue) {
        $scope.getTableData();
    });

    $scope.init();
}]);
