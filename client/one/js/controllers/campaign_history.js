/* globals oneApp,constants */
oneApp.controller('CampaignHistoryCtrl', ['$scope', '$state', '$modal', 'api', function ($scope, $state, $modal, api) { // eslint-disable-line max-len
    $scope.settings = {};
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

    $scope.getHistory = function () {
        $scope.requestInProgress = true;
        $scope.errors = {};

        if ($scope.hasPermission('zemauth.can_view_new_history_backend')) {
            var order = (!$scope.orderAsc && '-' || '') + $scope.order,
                params = {
                    campaign: $state.params.id,
                    level: constants.historyLevel.CAMPAIGN,
                };
            api.history.get(params, order).then(
                function (data) {
                    $scope.history = data.history;
                }
            ).finally(function () {
                $scope.requestInProgress = false;
            });
        } else {
            api.campaignHistory.get($state.params.id).then(
                function (data) {
                    $scope.history = data.history;
                }
            ).finally(function () {
                $scope.requestInProgress = false;
            });
        }
    };

    $scope.getHistory();
}]);
