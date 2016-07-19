/* globals oneApp */
'use strict';

oneApp.directive('zemGridHeaderCellData', ['$timeout', 'zemGridUIService', function ($timeout, zemGridUIService) {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            column: '=',
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_header_cell_data.html',
        controller: ['zemGridConstants', function (zemGridConstants) {
            var vm = this;
            vm.setOrder = setOrder;
            vm.getOrderClass = getOrderClass;

            function getOrderClass () {
                if (vm.column.order === zemGridConstants.gridColumnOrder.DESC) {
                    return 'ordered';
                }
                if (vm.column.order === zemGridConstants.gridColumnOrder.ASC) {
                    return 'ordered-reverse';
                }
                return null;
            }

            function setOrder () {
                toggleColumnOrder();

                var order = vm.column.data.orderField || vm.column.field;
                if (vm.column.order === zemGridConstants.gridColumnOrder.DESC) {
                    order = '-' + order;
                }

                // Resize columns to prevent flickering when rows are emptied
                zemGridUIService.resizeGridColumns(vm.grid);

                vm.grid.meta.service.setOrder(order, true);
            }

            function toggleColumnOrder ()  {
                switch (vm.column.order) {
                case zemGridConstants.gridColumnOrder.DESC:
                    vm.column.order = zemGridConstants.gridColumnOrder.ASC;
                    break;
                case zemGridConstants.gridColumnOrder.ASC:
                    vm.column.order = zemGridConstants.gridColumnOrder.DESC;
                    break;
                default:
                    vm.column.order = vm.column.data.initialOrder || zemGridConstants.gridColumnOrder.DESC;
                }
            }

        }],
    };
}]);
