/* globals oneApp */
'use strict';

oneApp.directive('zemGridCellBaseField', ['zemGridDataFormatter', function (zemGridDataFormatter) {

    function updateRow (ctrl) {
        ctrl.parsedValue = 'N/A';
        if (ctrl.data) {
            ctrl.parsedValue = zemGridDataFormatter.formatValue(ctrl.data.value, ctrl.column.data);
        }
    }

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
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_base_field.html',
        link: function (scope, element, attributes, ctrl) {
            scope.$watch('ctrl.row', function () {
                updateRow(ctrl);
            });
        },
        controller: [function () {}],
    };
}]);
