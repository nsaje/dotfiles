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
            col: '=',
            data: '=',
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell.html',
        controller: ['zemGridUIService', function (zemGridUIService) {
            this.toggleCollapse = function () {
                this.grid.meta.api.setCollapsedRows(this.row, !this.row.collapsed);
            };

            this.getBreakdownColumnStyle = function () {
                if (!this.row) return; // can happen - temporary; fix is part of Breakdown directive PR
                return zemGridUIService.getBreakdownColumnClass(this.row);
            };
        }],
    };
}]);
