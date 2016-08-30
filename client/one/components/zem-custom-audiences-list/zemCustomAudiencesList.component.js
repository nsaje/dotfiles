/* globals oneApp */
'use strict';

oneApp.directive('zemCustomAudiencesList', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        templateUrl: '/components/zem-custom-audiences-list/zemCustomAudiencesList.component.html',
        controllerAs: 'ctrl',
        controller: 'ZemCustomAudiencesListCtrl',
    };
}]);

oneApp.controller('ZemCustomAudiencesListCtrl', ['$scope', function ($scope) {
    $scope.audiences = [{
        id: 1,
        name: "Test audience 1",
    },{
        id: 2,
        name: "Test audience 2",
    },{
        id: 3,
        name: "Test audience 3",
    },{
        id: 4,
        name: "Test audience 4",
    }];
}]);
