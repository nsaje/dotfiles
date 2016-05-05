/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridCell', ['config', function (config) {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            position: '=',
            cell: '=',
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell.html',
        controller: ['zemGridService', function (zemGridUtil) {
            this.toggleCollapse = function () {
                zemGridUtil.toggleCollapse(this.grid, this.row);
            };

            this.getCellStyle = function () {
                var width = 'auto';
                if (this.grid.ui.columnWidths[this.position]) {
                    width = this.grid.ui.columnWidths[this.position] + 'px';
                }
                return {'min-width': width};
            };
        }],
    };
}]);
