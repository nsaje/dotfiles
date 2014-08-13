/*globals oneApp,constants,options,moment*/
oneApp.controller('CampaignAgencyCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.settings = {};
    $scope.options = options;

    $scope.getSettings = function (id) {
        api.campaignSettings.get(id).then(
            function (data) {
                $scope.settings = data.settings;
            },
            function (data) {
                // error
                return;
            }
        );
    };
}]);
