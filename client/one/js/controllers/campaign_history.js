/* globals angular, constants */
angular.module('one.legacy').controller('CampaignHistoryCtrl', function ($scope, $state) { // eslint-disable-line max-len
    $scope.params = {
        campaign: $state.params.id,
        level: constants.historyLevel.CAMPAIGN,
    };
    $scope.setActiveTab();
});
