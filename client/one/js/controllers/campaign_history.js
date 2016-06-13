/* globals oneApp */
oneApp.controller('CampaignHistoryCtrl', ['$scope', '$state', '$modal', 'api', function ($scope, $state, $modal, api) { // eslint-disable-line max-len
    $scope.settings = {};
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
    };

    $scope.getHistory = function () {
        $scope.requestInProgress = true;
        $scope.errors = {};

        if ($scope.hasPermission('zemauth.can_view_new_history_backend')) {
            api.history.get({campaign: $state.params.id}, (!$scope.orderAsc && '-' || '') + $scope.order).then(
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
