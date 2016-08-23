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
        controller: ['$scope', 'zemGridConstants', function ($scope, zemGridConstants) {
            var vm = this;
            var pubsub = this.grid.meta.pubsub;
            var orderService = this.grid.meta.orderService;

            vm.model = {};
            vm.setOrder = setOrder;

            initialize();

            function initialize () {
                pubsub.register(pubsub.EVENTS.EXT_ORDER_UPDATED, $scope, updateModel);
                $scope.$watch('ctrl.column', updateModel);
            }

            function updateModel () {
                vm.model.order = orderService.getColumnOrder(vm.column);
                vm.model.orderClass = getOrderClass();
            }


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
                var order = toggleOrder(vm.model.order);
                orderService.setColumnOrder(vm.column, order);
            }

            function toggleOrder (order) {
                switch (order) {
                case zemGridConstants.gridColumnOrder.DESC:
                    return zemGridConstants.gridColumnOrder.ASC;
                case zemGridConstants.gridColumnOrder.ASC:
                    return zemGridConstants.gridColumnOrder.DESC;
                default:
                    return vm.column.data.initialOrder || zemGridConstants.gridColumnOrder.DESC;
                }
            }
        }],
    };
}]);
