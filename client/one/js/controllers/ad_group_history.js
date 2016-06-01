/* globals oneApp */
oneApp.controller('AdGroupHistoryCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.alerts = [];
    $scope.history = [];
    $scope.orderField = 'datetime';
    $scope.orderReverse = true;
    $scope.requestInProgress = false;

    $scope.getSettings = function (id) {
        $scope.requestInProgress = true;
        api.adGroupAgency.get(id).then(
            function (data) {
                $scope.history = data.history;
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

    $scope.getSettings($state.params.id);
}]);
