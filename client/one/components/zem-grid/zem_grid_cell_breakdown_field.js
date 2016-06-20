/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellBreakdownField', [function () {

    var LEVELS_WITH_INTERNAL_LINKS = [
        constants.level.ALL_ACCOUNTS,
        constants.level.ACCOUNTS,
        constants.level.CAMPAIGNS,
    ];

    function updateRow (ctrl) {
        if (ctrl.data) {
            ctrl.fieldType = getFieldType(ctrl.grid.meta.data.level, ctrl.row.level);
        }
    }

    function getFieldType (level, rowLevel) {
        // Display internal link for rows level 1 on 'All acounts', 'Account' or 'Campaign' level
        if (LEVELS_WITH_INTERNAL_LINKS.indexOf(level) !== -1 && rowLevel === 1) {
            return 'internalLink';
        }
        return 'base';
    }

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
            scope.$watch('ctrl.row', function () {
                updateRow(ctrl);
            });
        },
        controller: [function () {}],
    };
}]);
