/* globals oneApp, constants */
'use strict';

oneApp.directive('zemGridCellBreakdownField', [function () {

    var BREAKDOWNS_WITH_INTERNAL_LINKS = [
        constants.breakdown.ACCOUNT,
        constants.breakdown.CAMPAIGN,
        constants.breakdown.AD_GROUP,
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
        controller: ['$scope', 'zemGridConstants', 'zemGridUIService', function ($scope, zemGridConstants, zemGridUIService) { // eslint-disable-line max-len
            var vm = this;
            vm.types = zemGridConstants.gridColumnTypes;
            vm.getBreakdownColumnStyle = getBreakdownColumnStyle;

            $scope.$watch('ctrl.row', update);
            $scope.$watch('ctrl.data', update);

            function update () {
                if (vm.row) {
                    vm.fieldType = getFieldType(vm.grid.meta.data.breakdown, vm.row.level);
                }
            }

            function getBreakdownColumnStyle () {
                if (!vm.row) return; // can happen because of virtual scroll; TODO: find better solution
                return zemGridUIService.getBreakdownColumnStyle(vm.row);
            }

            function getFieldType (breakdown, rowLevel) {
                // Footer row
                if (rowLevel === 0) {
                    return zemGridConstants.gridColumnTypes.TOTALS_LABEL;
                }
                // Display internal links for rows on first level in 'Account', 'Campaign' or 'Ad Group' breakdowns
                if (BREAKDOWNS_WITH_INTERNAL_LINKS.indexOf(breakdown) !== -1 && rowLevel === 1) {
                    return zemGridConstants.gridColumnTypes.INTERNAL_LINK;
                }
                return zemGridConstants.gridColumnTypes.BASE_FIELD;
            }
        }],
    };
}]);
