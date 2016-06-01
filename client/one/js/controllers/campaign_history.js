/* globals oneApp */
oneApp.controller('CampaignHistoryCtrl', ['$scope', '$state', '$modal', 'api', function ($scope, $state, $modal, api) { // eslint-disable-line max-len
    $scope.settings = {};
    $scope.history = [];
    $scope.requestInProgress = false;
    $scope.orderField = 'datetime';
    $scope.orderReverse = true;

    $scope.getSettings = function () {
        $scope.requestInProgress = true;
        $scope.errors = {};
        api.campaignHistory.get($state.params.id).then(
            function (data) {
                $scope.history = data.history;
            },
            function () {
                // error
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.getSettings();
}]);
