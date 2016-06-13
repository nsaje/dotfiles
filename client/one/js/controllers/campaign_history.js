/* globals oneApp */
oneApp.controller('CampaignHistoryCtrl', ['$scope', '$state', '$modal', 'api', function ($scope, $state, $modal, api) { // eslint-disable-line max-len
    $scope.settings = {};
    $scope.history = [];
    $scope.requestInProgress = false;
    $scope.orderField = 'datetime';
    $scope.orderReverse = true;

    $scope.getHistory = function () {
        $scope.requestInProgress = true;
        $scope.errors = {};

        if ($scope.hasPermission('zemauth.can_view_new_history_backend')) {
            api.history.get({campaign: $state.params.id}).then(
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
