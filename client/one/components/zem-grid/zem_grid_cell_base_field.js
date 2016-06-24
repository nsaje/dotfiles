/* globals oneApp */
'use strict';

oneApp.directive('zemGridCellBaseField', ['zemGridDataFormatter', function (zemGridDataFormatter) {

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
                updateRow();
            });

            function updateRow () {
                var value = ctrl.data ? ctrl.data.value : undefined;
                ctrl.parsedValue = zemGridDataFormatter.formatValue(value, ctrl.column.data);
            }
        },
        controller: [function () {}],
    };
}]);
