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

            pubsub.register(pubsub.EVENTS.BODY_HORIZONTAL_SCROLL, function (event, leftOffset) {
                handleHorizontalScroll(leftOffset);
            });
        },
        controller: [function () {
            this.setOrder = function (column) {
                var order = this.grid.meta.service.getOrder();

                if (order === column.field) {
                    order = '-' + column.field;
                } else if (order === '-' + column.field) {
                    order = column.field;
                } else if (column.initialOrder === 'asc') {
                    order = column.field;
                } else {
                    order = '-' + column.field;
                }

                this.grid.meta.service.setOrder(order, true);
            };
        }],
    };
}]);
