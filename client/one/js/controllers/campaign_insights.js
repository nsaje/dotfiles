/* globals angular, constants */
angular.module('one.legacy').controller('CampaignInsightsCtrl', function ($scope, $state, zemNavigationNewService) { // eslint-disable-line max-len
    $scope.params = {
        campaign: $state.params.id,
        level: constants.historyLevel.CAMPAIGN,
    };
    $scope.setActiveTab();

    function loadEntity () {
        $scope.entity = zemNavigationNewService.getActiveEntity();
        zemNavigationNewService.onActiveEntityChange(function () {
            $scope.entity = zemNavigationNewService.getActiveEntity();
        });
    }

    loadEntity();
});
