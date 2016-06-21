/* globals oneApp,constants */
oneApp.controller('AccountHistoryCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.params = {
        account: $state.params.id,
        level: constants.historyLevel.ACCOUNT,
    };
}]);
