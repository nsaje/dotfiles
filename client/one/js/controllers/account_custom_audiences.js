/* globals angular */
'use strict';

angular.module('one.legacy').controller('AccountCustomAudiencesCtrl', ['$scope', '$state', function ($scope, $state) { // eslint-disable-line max-len
    $scope.accountId = $state.params.id;
}]);
