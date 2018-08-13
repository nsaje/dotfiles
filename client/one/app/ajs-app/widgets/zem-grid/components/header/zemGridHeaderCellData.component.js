angular.module('one.widgets').directive('zemGridHeaderCellData', function() {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            column: '=',
            grid: '=',
        },
        template: require('./zemGridHeaderCellData.component.html'),
        controller: function($scope, zemGridConstants) {
            var vm = this;
            var pubsub = this.grid.meta.pubsub;
            var orderService = this.grid.meta.orderService;

            vm.model = {};
            vm.setOrder = setOrder;
            vm.maxNameLength = 22;

            initialize();

            function initialize() {
                pubsub.register(
                    pubsub.EVENTS.DATA_UPDATED,
                    $scope,
                    setBreakdownByStructureText
                );
                pubsub.register(
                    pubsub.EVENTS.EXT_ORDER_UPDATED,
                    $scope,
                    updateModel
                );
                $scope.$watch('ctrl.column', updateModel);
            }

            function updateModel() {
                vm.model.order = orderService.getColumnOrder(vm.column);
                vm.model.orderClass = getOrderClass();
            }

            function setBreakdownByStructureText() {
                vm.column.data.breakdownByStructureText = null;

                if (!vm.grid || !vm.grid.meta || !vm.grid.meta.api) {
                    return;
                }

                if (
                    vm.column.type !==
                    zemGridConstants.gridColumnTypes.BREAKDOWN
                ) {
                    return;
                }

                var breakdown = vm.grid.meta.api.getBreakdown();
                var structureBreakdowns = vm.grid.meta.api.getMetaData()
                    .breakdownGroups.structure.breakdowns;

                if (breakdown[1]) {
                    structureBreakdowns.forEach(function(b) {
                        if (b.query === breakdown[1].query) {
                            vm.column.data.breakdownByStructureText =
                                ' > ' + breakdown[1].name;
                        }
                    });
                }
            }

            function getOrderClass() {
                if (vm.column.order === zemGridConstants.gridColumnOrder.DESC) {
                    return 'ordered';
                }
                if (vm.column.order === zemGridConstants.gridColumnOrder.ASC) {
                    return 'ordered-reverse';
                }
                return null;
            }

            function setOrder() {
                var order = toggleOrder(vm.model.order);
                orderService.setColumnOrder(vm.column, order);
            }

            function toggleOrder(order) {
                switch (order) {
                    case zemGridConstants.gridColumnOrder.DESC:
                        return zemGridConstants.gridColumnOrder.ASC;
                    case zemGridConstants.gridColumnOrder.ASC:
                        return zemGridConstants.gridColumnOrder.DESC;
                    default:
                        return (
                            vm.column.data.initialOrder ||
                            zemGridConstants.gridColumnOrder.DESC
                        );
                }
            }
        },
    };
});
