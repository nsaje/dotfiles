/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridCell', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            cell: '=',
            columnsWidths: '@',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell.html',
        controller: ['$scope', function ($scope) {
            $scope.getCellStyle = function (index) {
                var width = 'auto';
                if ($scope.columnsWidths[index]) {
                    width = $scope.columnsWidths[index] + 'px';
                }
                return {'min-width': width};
            };
        }],
    };
}]);
