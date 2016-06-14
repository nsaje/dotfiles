/* globals oneApp */
oneApp.controller('AccountHistoryCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.history = [];
    $scope.requestInProgress = false;
    $scope.order = 'datetime';
    $scope.orderAsc = false;

    $scope.changeOrder = function(field) {
        $scope.order = field;
        $scope.orderAsc = !$scope.orderAsc;

        $scope.getHistory();
    };

    $scope.getOrderClass = function (field) {
        if ($scope.order !== field) {
            return '';
        }

        if ($scope.orderAsc) {
            return 'ordered-reverse';
        } else {
            return 'ordered';  
        }
    }

    $scope.getHistory = function () {
        $scope.requestInProgress = true;

        if ($scope.hasPermission('zemauth.can_view_new_history_backend')) {
            var order = (!$scope.orderAsc && '-' || '') + $scope.order,
                params = {
                    account: $state.params.id, 
                    level: constants.historyLevel.ACCOUNT,
                };
            api.history.get(params, order).then(
                function (data) {
                    $scope.history = data.history;
                }
            ).finally(function () {
                $scope.requestInProgress = false;
            });
        } else {
            api.accountHistory.get($state.params.id).then(
                function (data) {
                    $scope.history = data.history;
                }
            ).finally(function () {
                $scope.requestInProgress = false;
            });
        }
    };

    $scope.refreshPage = function () {
        zemNavigationService.reload();
        $scope.getHistory();
    };

    $scope.getHistory();

    $scope.getName = function (user) {
        return user.name;
    };
}]);
