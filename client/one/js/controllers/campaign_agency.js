/* globals oneApp, options */
oneApp.controller('CampaignAgencyCtrl', ['$scope', '$state', '$modal', 'api', 'zemNavigationService', function ($scope, $state, $modal, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.settings = {};
    $scope.history = [];
    $scope.requestInProgress = false;
    $scope.orderField = 'datetime';
    $scope.orderReverse = true;

    $scope.getSettings = function (discarded) {
        $scope.requestInProgress = true;
        $scope.errors = {};
        api.campaignAgency.get($state.params.id).then(
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
