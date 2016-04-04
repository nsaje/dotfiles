/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridRow', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            row: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_row.html',
        controller: ['$scope', function ($scope) {
            $scope.getRowClass = function () {
                var classes = [];
                classes.push('level-' + this.row.level);

                if (this.row.level === $scope.dataSource.breakdowns.length) {
                    classes.push('level-last');
                }
                return classes;
            };
        }],
    };
}]);
