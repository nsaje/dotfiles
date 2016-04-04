/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridDebug', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_debug.html',
        controller: ['$scope', function ($scope) {
            $scope.DEBUG_BREAKDOWNS = {'ad_group': true, 'age': true, 'sex': false, 'date': true};
            $scope.DEBUG_APPLY_BREAKDOWN = function () {
                var breakdowns = [];
                angular.forEach($scope.DEBUG_BREAKDOWNS, function (value, key) {
                    if (value) breakdowns.push(key);
                });
                $scope.dataSource.breakdowns = breakdowns;
                $scope.dataSource.defaultPagination = [2, 3, 5, 7];
                $scope.load();
            };
        }],
    };
}]);
