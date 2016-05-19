/* globals oneApp */
oneApp.controller('AccountHistoryCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.history = [];
    $scope.requestInProgress = false;

    $scope.getSettings = function () {
        $scope.requestInProgress = true;
        api.accountHistory.get($state.params.id).then(
            function (data) {
                $scope.history = data.history;
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.refreshPage = function () {
        zemNavigationService.reload();
        $scope.getSettings();
    };

    $scope.getSettings();

    $scope.getName = function (user) {
        return user.name;
    };
}]);
