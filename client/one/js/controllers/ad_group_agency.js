/* globals oneApp */
oneApp.controller('AdGroupAgencyCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
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
        zemNavigationService.reloadAdGroup($state.params.id);
        $scope.getSettings($state.params.id);
    };

    $scope.archiveAdGroup = function () {
        if ($scope.canArchive) {
            zemNavigationService.notifyAdGroupReloading($scope.adGroup.id, true);
            api.adGroupArchive.archive($scope.adGroup.id).then(function () {
                $scope.refreshPage();
            }, function () {
                zemNavigationService.notifyAdGroupReloading($scope.adGroup.id, false);
            });
        }
    };

    $scope.restoreAdGroup = function () {
        if ($scope.canRestore) {
            zemNavigationService.notifyAdGroupReloading($scope.adGroup.id, true);
            api.adGroupArchive.restore($scope.adGroup.id).then(function () {
                $scope.refreshPage();
            }, function () {
                zemNavigationService.notifyAdGroupReloading($scope.adGroup.id, false);
            });
        }
    };

    $scope.getSettings($state.params.id);
}]);
