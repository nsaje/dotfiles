/*globals oneApp,constants,options,moment*/
oneApp.controller('CampaignAgencyCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.settings = {};
    $scope.accountManagers = {};
    $scope.options = options;

    $scope.getSettings = function (id) {
        api.campaignSettings.get(id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.accountManagers = data.accountManagers;
                $scope.salesReps = data.salesReps;
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.getSettings($state.params.id);
}]);
