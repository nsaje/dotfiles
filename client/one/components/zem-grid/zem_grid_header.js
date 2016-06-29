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

                initializeOrder();

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

            function initializeOrder () {
                var order = vm.grid.meta.service.getOrder();
                if (!order) return;

                var direction = zemGridConstants.gridColumnOrder.ASC;
                if (order[0] === '-') {
                    direction = zemGridConstants.gridColumnOrder.DESC;
                    order = order.substr(1);
                }

                vm.grid.header.columns.forEach(function (column) {
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

            function toggleColumnOrder (column)  {
                vm.grid.header.columns.forEach(function (c) {
                    if (column !== c) {
                        c.order = zemGridConstants.gridColumnOrder.NONE;
                    }
                });

                switch (column.order) {
                case zemGridConstants.gridColumnOrder.DESC:
                    column.order = zemGridConstants.gridColumnOrder.ASC;
                    break;
                case zemGridConstants.gridColumnOrder.ASC:
                    column.order = zemGridConstants.gridColumnOrder.DESC;
                    break;
                default:
                    if (column.data.initialOrder) {
                        column.order = column.data.initialOrder;
                    } else {
                        column.order = zemGridConstants.gridColumnOrder.DESC;
                    }
                }
            }

            function setOrder (column) {
                toggleColumnOrder(column);

                var order = column.field;
                if (column.order === zemGridConstants.gridColumnOrder.DESC) {
                    order = '-' + column.field;
                }

                // Resize columns to prevent flickering when rows are emptied
                zemGridUIService.resizeGridColumns(vm.grid);

                vm.grid.meta.service.setOrder(order, true);
            }
        }],
    };
}]);
