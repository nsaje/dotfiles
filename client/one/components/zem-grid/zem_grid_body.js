/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridBody', ['$timeout', 'config', 'zemGridConstants', function ($timeout, config, zemGridConstants) {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
            pubsub: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_body.html',
        link: function (scope, element) {
            var lastScrollLeft = 0;
            var lastScrollTop = 0;
            var pubsub = scope.ctrl.pubsub;

            function handleScroll (event) {
                if (lastScrollLeft !== event.target.scrollLeft) {
                    lastScrollLeft = event.target.scrollLeft;
                    pubsub.notify(
                        pubsub.EVENTS.BODY_HORIZONTAL_SCROLL,
                        event.target.scrollLeft
                    );
                }

                if (lastScrollTop !== event.target.scrollTop) {
                    lastScrollTop = this.scrollTop;
                    pubsub.notify(
                        pubsub.EVENTS.BODY_VERTICAL_SCROLL,
                        event.target.scrollTop
                    );
                }
            }

            scope.$watch('ctrl.grid.body.rows', function (rows) {
                if (rows) {
                    $timeout(function () {
                        // Calculate columns widths after body rows are rendered
                        var columns = element.querySelectorAll('.zem-grid-cell');
                        columns.each(function (index, column) {
                            var columnWidth = column.offsetWidth;
                            if (scope.ctrl.grid.ui.columnWidths[index] < columnWidth) {
                                scope.ctrl.grid.ui.columnWidths[index] = columnWidth;
                            }
                        });
                    }, 0, false);
                }
            });

            element.on('scroll', handleScroll);
        },
        controller: [function () {
        }],
    };
}]);
