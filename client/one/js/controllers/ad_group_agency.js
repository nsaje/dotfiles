/*globals oneApp,moment*/
oneApp.controller('AdGroupAgencyCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.alerts = [];
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
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.requestInProgress = false;
            },
            function (data) {
                // error
                $scope.requestInProgress = false;
                return;
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
