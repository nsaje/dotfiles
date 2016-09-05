/* globals angular, constants */
angular.module('one.legacy').controller('AdGroupHistoryCtrl', ['$scope', '$state', function ($scope, $state) { // eslint-disable-line max-len
    $scope.params = {
        adGroup: $state.params.id,
        level: constants.historyLevel.AD_GROUP,
    };
    $scope.setActiveTab();
}]);
