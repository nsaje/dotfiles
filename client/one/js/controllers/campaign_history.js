/* globals oneApp,constants */
oneApp.controller('CampaignHistoryCtrl', ['$scope', '$state', function ($scope, $state) { // eslint-disable-line max-len
    $scope.params = {
        campaign: $state.params.id,
        level: constants.historyLevel.CAMPAIGN,
    };
}]);
