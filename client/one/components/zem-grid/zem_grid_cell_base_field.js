/* globals oneApp */
'use strict';

oneApp.directive('zemGridCellBaseField', ['zemGridDataFormatter', 'zemGridUIService', function (zemGridDataFormatter, zemGridUIService) { // eslint-disable-line max-len

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
            scope.$watch('ctrl.row', update);
            scope.$watch('ctrl.data', update);

            function update () {
                var value = ctrl.data ? ctrl.data.value : undefined;
                ctrl.parsedValue = zemGridDataFormatter.formatValue(value, ctrl.column.data);

                ctrl.goalStatusClass = '';
                if (ctrl.data) {
                    ctrl.goalStatusClass = zemGridUIService.getFieldGoalStatusClass(ctrl.data.goalStatus);
                }
            }
        },
        controller: [function () {}],
    };
}]);
