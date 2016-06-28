/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellBreakdownField', ['zemGridConstants', function (zemGridConstants) {

    var BREAKDOWNS_WITH_INTERNAL_LINKS = [
        constants.breakdown.ACCOUNT,
        constants.breakdown.CAMPAIGN,
        constants.breakdown.AD_GROUP,
    ];

    function getFieldType (breakdown, rowLevel) {
        if (rowLevel === 0) {
            return zemGridConstants.gridColumnTypes.TOTALS_LABEL;
        }
        // Display internal links for rows on first level in 'Account', 'Campaign' or 'Ad Group' breakdowns
        if (BREAKDOWNS_WITH_INTERNAL_LINKS.indexOf(breakdown) !== -1 && rowLevel === 1) {
            return zemGridConstants.gridColumnTypes.INTERNAL_LINK;
        }
        return zemGridConstants.gridColumnTypes.BASE_FIELD;
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
            ctrl.types = zemGridConstants.gridColumnTypes;

            scope.$watch('ctrl.row', update);
            scope.$watch('ctrl.data', update);

            function update () {
                if (ctrl.row) {
                    ctrl.fieldType = getFieldType(ctrl.grid.meta.data.breakdown, ctrl.row.level);
                }
            }
        },
        controller: ['zemGridUIService', function (zemGridUIService) {
            var vm = this;
            vm.getBreakdownColumnStyle = getBreakdownColumnStyle;

            function getBreakdownColumnStyle () {
                if (!this.row) return; // can happen because of virtual scroll; TODO: find better solution
                return zemGridUIService.getBreakdownColumnStyle(vm.row);
            }
        }],
    };
}]);
