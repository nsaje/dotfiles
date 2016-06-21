/* globals oneApp,constants */
oneApp.controller('AccountHistoryCtrl', ['$scope', '$state', function ($scope, $state) { // eslint-disable-line max-len
    $scope.params = {
        account: $state.params.id,
        level: constants.historyLevel.ACCOUNT,
    };
}]);
