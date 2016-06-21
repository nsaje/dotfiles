/* globals oneApp,constants */
oneApp.controller('CampaignHistoryCtrl', ['$scope', '$state', '$modal', 'api', function ($scope, $state, $modal, api) { // eslint-disable-line max-len
    $scope.params = {
        campaign: $state.params.id,
        level: constants.historyLevel.CAMPAIGN,
    };
}]);
