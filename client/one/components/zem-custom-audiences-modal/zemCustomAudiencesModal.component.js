/* globals angular */
'use strict';

angular.module('one.legacy').directive('zemCustomAudiencesModal', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        templateUrl: '/components/zem-custom-audiences-modal/zemCustomAudiencesModal.component.html',
        controllerAs: 'ctrl',
        controller: 'ZemCustomAudiencesModalCtrl',
    };
}]);

angular.module('one.legacy').controller('ZemCustomAudiencesModalCtrl', ['$scope', function ($scope) {
    $scope.audience = {ruleId: 1, refererRuleId: 1};
    $scope.pixels = [{name: 'Test pixel 1', id: 1}, {name: 'Test pixel 2', id: 2}];
    $scope.rules = [{id: 1, name: 'Anyone who visited your website'}, {id: 2, name: 'People who visited specific web pages'}];
    $scope.refererRules = [{id: 1, name: 'URL equals'}, {id: 2, name: 'URL contains'}];
    $scope.ttlDays = [{value: 7, name: '7'}, {value: 30, name: '30'}, {value: 90, name: '90'}];

    $scope.showRefererRules = function () {
        if ($scope.audience.ruleId === 2) {
            return true;
        }
        return false;
    };
}]);
