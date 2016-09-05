/* globals angular, constants */
'use strict';

angular.module('one.legacy').directive('zemGridCellBreakdownField', [function () {

    var BREAKDOWNS_WITH_INTERNAL_LINKS = [
        constants.breakdown.ACCOUNT,
        constants.breakdown.CAMPAIGN,
        constants.breakdown.AD_GROUP,
    ];

    var BREAKDOWNS_WITH_EXTERNAL_LINK = [
        constants.breakdown.CONTENT_AD,
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
        controller: ['$scope', 'config', 'zemGridConstants', 'zemGridUIService', function ($scope, config, zemGridConstants, zemGridUIService) { // eslint-disable-line max-len
            var vm = this;
            var collapseService = vm.grid.meta.collapseService;

            vm.config = config;
            vm.types = zemGridConstants.gridColumnTypes;
            vm.collapsable = false;
            vm.collapsed = false;
            vm.toggleCollapse = toggleCollapse;
            vm.getBreakdownColumnStyle = getBreakdownColumnStyle;

            initialize();

            function initialize () {
                var pubsub = vm.grid.meta.pubsub;
                $scope.$watch('ctrl.row', updateModel);
                $scope.$watch('ctrl.data', updateModel);
                pubsub.register(pubsub.EVENTS.EXT_COLLAPSE_UPDATED, $scope, updateModel);

                updateModel();
            }

            function updateModel () {
                if (!vm.row) return;

                vm.fieldType = getFieldType(vm.grid.meta.data.breakdown, vm.row.level);
                vm.collapsable = collapseService.isRowCollapsable(vm.row);
                vm.collapsed = collapseService.isRowCollapsed(vm.row);
            }

            function getBreakdownColumnStyle () {
                if (!vm.row) return; // can happen because of virtual scroll; TODO: find better solution
                return zemGridUIService.getBreakdownColumnStyle(vm.grid, vm.row);
            }

            function toggleCollapse () {
                return collapseService.setRowCollapsed(vm.row, !vm.collapsed);
            }

            function getFieldType (breakdown, rowLevel) {
                // Footer row
                if (rowLevel === zemGridConstants.gridRowLevel.FOOTER) {
                    return zemGridConstants.gridColumnTypes.TOTALS_LABEL;
                }
                // Display internal links for rows on first level in 'Account', 'Campaign' or 'Ad Group' breakdowns
                if (BREAKDOWNS_WITH_INTERNAL_LINKS.indexOf(breakdown) !== -1 &&
                    rowLevel === zemGridConstants.gridRowLevel.BASE) {
                    return zemGridConstants.gridColumnTypes.INTERNAL_LINK;
                }

                if (BREAKDOWNS_WITH_EXTERNAL_LINK.indexOf(breakdown) !== -1 &&
                    rowLevel === zemGridConstants.gridRowLevel.BASE) {
                    return zemGridConstants.gridColumnTypes.EXTERNAL_LINK;
                }

                return zemGridConstants.gridColumnTypes.BASE_FIELD;
            }
        }],
    };
}]);
