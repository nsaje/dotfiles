/*globals oneApp,moment*/
oneApp.controller('AdGroupAgencyCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.settings = {};
    $scope.actionIsWaiting = false;
    $scope.errors = {};
    $scope.alerts = [];
    $scope.saveRequestInProgress = false;
    $scope.saved = null;
    $scope.discarded = null;
    $scope.history = [];
    $scope.canArchive = false;
    $scope.canRestore = true;
    $scope.orderField = 'datetime';
    $scope.orderReverse = true;

    $scope.getSettings = function (id) {
        api.adGroupAgency.get(id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.actionIsWaiting = data.actionIsWaiting;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.discardSettings = function () {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.saveRequestInProgress = true;
        $scope.errors = {};
        api.adGroupAgency.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.actionIsWaiting = data.actionIsWaiting;
                $scope.saveRequestInProgress = false;
                $scope.discarded = true;
            },
            function (data) {
                // error
                $scope.saveRequestInProgress = false;
                return;
            }
        );
    };

    $scope.saveSettings = function () {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.saveRequestInProgress = true;

        api.adGroupAgency.save($scope.settings).then(
            function (data) {
                $scope.errors = {};
                $scope.settings = data.settings;
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.actionIsWaiting = data.actionIsWaiting;
                $scope.saveRequestInProgress = false;
                $scope.saved = true;
            },
            function (data) {
                $scope.errors = data;
                $scope.saveRequestInProgress = false;
                $scope.saved = false;
            }
        );
    };

    $scope.archiveAdGroup = function () {
        api.adGroupArchive.archive($scope.adGroup.id).then(function () {
            api.navData.list().then(function (accounts) {
                $scope.refreshNavData(accounts);
                $scope.getModels();
            });
            $scope.getSettings($state.params.id);
        });
    };

    $scope.restoreAdGroup = function () {
        api.adGroupArchive.restore($scope.adGroup.id).then(function () {
            api.navData.list().then(function (accounts) {
                $scope.refreshNavData(accounts);
                $scope.getModels();
            });
            $scope.getSettings($state.params.id);
        });
    };

    $scope.getSettings($state.params.id);
}]);
