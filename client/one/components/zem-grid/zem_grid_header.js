/* globals oneApp */
'use strict';

oneApp.directive('zemGridHeader', ['$timeout', 'zemGridUIService', function ($timeout, zemGridUIService) {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_header.html',
        link: function (scope, element, attributes, ctrl) {
            var pubsub = ctrl.grid.meta.pubsub;
            ctrl.grid.header.ui.element = element;

            function resizeColumns () {
                $timeout(function () {
                    zemGridUIService.resizeGridColumns(ctrl.grid);
                }, 0, false);
            }

            function handleHorizontalScroll (leftOffset) {
                leftOffset = -1 * leftOffset;
                var translateCssProperty = 'translateX(' + leftOffset + 'px)';

                element.css({
                    '-webkit-transform': translateCssProperty,
                    '-ms-transform': translateCssProperty,
                    'transform': translateCssProperty,
                });
            }

            pubsub.register(pubsub.EVENTS.DATA_UPDATED, resizeColumns);
            pubsub.register(pubsub.EVENTS.METADATA_UPDATED, resizeColumns);
            resizeColumns();

            pubsub.register(pubsub.EVENTS.BODY_HORIZONTAL_SCROLL, function (event, leftOffset) {
                handleHorizontalScroll(leftOffset);
            });
        },
        controller: ['zemGridConstants', 'zemGridStorageService', function (zemGridConstants, zemGridStorageService) {
            var vm = this;
            vm.setOrder = setOrder;
            vm.getHeaderColumnClass = getHeaderColumnClass;
            vm.getHeaderColumnOrderClass = getHeaderColumnOrderClass;

            initialize();

            function initialize () {
                initializeColumns();
                vm.grid.meta.pubsub.register(vm.grid.meta.pubsub.EVENTS.METADATA_UPDATED, initializeColumns);
                vm.grid.meta.pubsub.register(vm.grid.meta.pubsub.EVENTS.DATA_UPDATED, initializeColumns);
            }

            function initializeColumns () {
                // Initialize header columns based on the stored data and default values
                zemGridStorageService.loadColumns(vm.grid);

                initializeOrder(vm.grid.meta.service.getOrder());

                vm.grid.header.visibleColumns = vm.grid.header.columns.filter(function (column) {
                    return column.visible;
                });

                if (vm.grid.meta.service.getBreakdownLevel() > 1) {
                    vm.grid.header.visibleColumns.unshift({
                        type: zemGridConstants.gridColumnTypes.COLLAPSE,
                    });
                }

                if (vm.grid.meta.options.enableSelection) {
                    vm.grid.header.visibleColumns.unshift({
                        type: zemGridConstants.gridColumnTypes.CHECKBOX,
                    });
                }
            }

            function initializeOrder (order) {
                if (!order) return;

                var direction = zemGridConstants.gridColumnOrder.ASC;
                if (order[0] === '-') {
                    direction = zemGridConstants.gridColumnOrder.DESC;
                    order = order.substr(1);
                }

                vm.grid.header.columns.forEach (function (column) {
                    if (column.field === order) {
                        column.order = direction;
                    } else {
                        column.order = zemGridConstants.gridColumnOrder.NONE;
                    }
                });
            }

            function getHeaderColumnClass (column) {
                return zemGridUIService.getHeaderColumnClass(vm.grid, column);
            }

            function getHeaderColumnOrderClass (column) {
                return zemGridUIService.getHeaderColumnOrderClass(vm.grid, column);
            }

            function setOrder (column) {
                var order = column.field;
                if (column.order === zemGridConstants.gridColumnOrder.ASC) {
                    order = '-' + column.field;
                }

                // Workaround - initialize order and resize columns (prevent flickering when rows are emptied)
                initializeOrder(order);
                zemGridUIService.resizeGridColumns(vm.grid);

                vm.grid.meta.service.setOrder(order, true);
            }
        }],
    };
}]);
