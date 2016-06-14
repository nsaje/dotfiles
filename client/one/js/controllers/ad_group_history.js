/* globals oneApp,constants */
oneApp.controller('AdGroupHistoryCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.alerts = [];
    $scope.history = [];
    $scope.requestInProgress = false;
    $scope.order = 'datetime';
    $scope.orderAsc = true;

    $scope.changeOrder = function (field) {
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
        }
        return 'ordered';
    };

    $scope.getHistory = function (id) {
        $scope.requestInProgress = true;
        if ($scope.hasPermission('zemauth.can_view_new_history_backend')) {
            var order = (!$scope.orderAsc && '-' || '') + $scope.order,
                params = {
                    adGroup: $state.params.id,
                    level: constants.historyLevel.AD_GROUP,
                };
            api.history.get(params, order).then(
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
