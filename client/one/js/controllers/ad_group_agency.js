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
    $scope.requestInProgress = false;

    $scope.getSettings = function (id) {
        $scope.requestInProgress = true;
        api.adGroupAgency.get(id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.actionIsWaiting = data.actionIsWaiting;
                $scope.requestInProgress = false;
            },
            function (data) {
                // error
                $scope.requestInProgress = false;
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

    $scope.refreshPage = function () {
        api.navData.list().then(function (accounts) {
            $scope.refreshNavData(accounts);
            $scope.getModels();
        });
        $scope.getSettings($state.params.id);
    };

    $scope.archiveAdGroup = function () {
        if ($scope.canArchive) {
            api.adGroupArchive.archive($scope.adGroup.id).then(function () {
                $scope.refreshPage();
            });
        }
    };

    $scope.restoreAdGroup = function () {
        if ($scope.canRestore) {
            api.adGroupArchive.restore($scope.adGroup.id).then(function () {
                $scope.refreshPage();
            });
        }
    };

    $scope.getSettings($state.params.id);
}]);
