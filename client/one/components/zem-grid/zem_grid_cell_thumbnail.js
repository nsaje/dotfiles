/* globals oneApp */
'use strict';

oneApp.directive('zemGridCellThumbnail', [function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            column: '=',
            row: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_thumbnail.html',
        controller: [function () {}],
    };
}]);
