/* globals oneApp */
'use strict';

oneApp.directive('zemGridCell', [function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            position: '=',
            field: '=',
            row: '=',
            grid: '=',
            pubsub: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell.html',
        controller: ['$scope', 'zemGridService', function ($scope, zemGridService) {
            this.toggleCollapse = function () {
                zemGridService.toggleCollapse(this.grid, this.row);
                $scope.ctrl.pubsub.notify($scope.ctrl.pubsub.EVENTS.ROWS_UPDATED);
            };

            this.getCellStyle = function () {
                return zemGridService.getCellStyle(this.grid, this.position);
            };
        }],
    };
}]);
