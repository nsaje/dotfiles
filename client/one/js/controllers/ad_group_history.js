/* globals oneApp,constants */
oneApp.controller('AdGroupHistoryCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.params = {
        adGroup: $state.params.id,
        level: constants.historyLevel.AD_GROUP,
    };
}]);
