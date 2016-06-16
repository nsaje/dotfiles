/* globals oneApp */
'use strict';

oneApp.directive('zemGridCellBreakdownField', [function () {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            data: '=',
            row: '=',
            column: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_cell_breakdown_field.html',
        link: function (scope, element, attributes, ctrl) {
            scope.$watch('ctrl.data', function () {
                if (ctrl.data) {
                    ctrl.fieldType = 'base';
                    // Display internal link for first breakdown level in 'All acounts', 'Account' or 'Campaign' view.
                    if (ctrl.row.level === 1 &&
                        ['all_accounts', 'accounts', 'campaigns'].indexOf(ctrl.grid.meta.data.level) !== -1
                    ) {
                        ctrl.fieldType = 'internalLink';
                    }
                }
            });
        },
        controller: [function () {}],
    };
}]);
