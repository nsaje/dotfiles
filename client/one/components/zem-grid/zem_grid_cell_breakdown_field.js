/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellBreakdownField', [function () {

    var LEVELS_WITH_INTERNAL_LINKS = [
        constants.level.ALL_ACCOUNTS,
        constants.level.ACCOUNTS,
        constants.level.CAMPAIGNS,
    ];

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
                    // Display internal link for row level 1 on 'All acounts', 'Account' or 'Campaign' level.
                    if (ctrl.row.level === 1 && LEVELS_WITH_INTERNAL_LINKS.indexOf(ctrl.grid.meta.data.level) !== -1) {
                        ctrl.fieldType = 'internalLink';
                    }
                }
            });
        },
        controller: [function () {}],
    };
}]);
