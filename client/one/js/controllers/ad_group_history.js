/* globals oneApp */
oneApp.controller('AdGroupHistoryCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.alerts = [];
    $scope.history = [];
    $scope.orderField = 'datetime';
    $scope.orderReverse = true;
    $scope.requestInProgress = false;

    $scope.getHistory = function (id) {
        $scope.requestInProgress = true;
        if ($scope.hasPermission('zemauth.can_view_new_history_backend')) {
            api.history.get({adGroup: $state.params.id}).then(
                function (data) {
                    $scope.history = data.history;
                }
            ).finally(function () {
                $scope.requestInProgress = false;
            });
        } else {
            api.adGroupHistory.get(id).then(
                function (data) {
                    $scope.history = data.history;
                }
            ).finally(function () {
                $scope.requestInProgress = false;
            });
        }
    };

    $scope.refreshPage = function () {
        zemNavigationService.reloadAdGroup($state.params.id);
        $scope.getHistory($state.params.id);
    };

    $scope.getHistory($state.params.id);
}]);
