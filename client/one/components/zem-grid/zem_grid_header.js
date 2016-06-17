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
        link: function postLink (scope, element) {
            var pubsub = scope.ctrl.grid.meta.pubsub;
            scope.ctrl.grid.header.ui.element = element;

            function resizeColumns () {
                $timeout(function () {
                    zemGridUIService.resizeGridColumns(scope.ctrl.grid);
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
        controller: ['zemGridStorageService', function (zemGridStorageService) {
            var vm = this;
            vm.setOrder = setOrder;
            vm.getHeaderColumnClass = getHeaderColumnClass;

            initialize();

            function initialize () {
                // Initialize header columns based on the stored data and default values
                zemGridStorageService.loadColumns(vm.grid);
                initVisibleColumns();
                vm.grid.meta.pubsub.register(vm.grid.meta.pubsub.EVENTS.DATA_UPDATED, initVisibleColumns);
            }

            function initVisibleColumns () {
                vm.grid.header.visibleColumns = vm.grid.header.columns.filter(function (column) {
                    return column.visible;
                });

                if (vm.grid.meta.service.getBreakdownLevel() > 1) {
                    vm.grid.header.visibleColumns.unshift({
                        type: 'collapse',
                    });
                }
                vm.grid.header.visibleColumns.unshift({
                    type: 'checkbox',
                });
            }

            function getHeaderColumnClass (column) {
                return zemGridUIService.getHeaderColumnClass(vm.grid, column);
            }

            function setOrder (column) {
                var order = vm.grid.meta.service.getOrder();

                if (order === column.field) {
                    order = '-' + column.field;
                } else if (order === '-' + column.field) {
                    order = column.field;
                } else if (column.data.initialOrder === 'asc') {
                    order = column.field;
                } else {
                    order = '-' + column.field;
                }

                vm.grid.meta.service.setOrder(order, true);
            }
        }],
    };
}]);
