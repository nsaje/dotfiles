/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridBody', ['$timeout', 'config', 'zemGridConstants', function ($timeout, config, zemGridConstants) {

    return {
        restrict: 'E',
        replace: true,
        require: '^zemGrid',
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            rows: '=',
            columnsWidths: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_body.html',
        link: function postLink (scope, element, attributes, zemGridController) {
            var lastScrollLeft = 0;
            var lastScrollTop = 0;
            function handleScroll (event) {
                if (lastScrollLeft !== event.target.scrollLeft) {
                    lastScrollLeft = event.target.scrollLeft;
                    zemGridController.broadcastEvent(
                        zemGridConstants.events.BODY_HORIZONTAL_SCROLL,
                        event.target.scrollLeft
                    );
                }

                if (lastScrollTop !== event.target.scrollTop) {
                    lastScrollTop = this.scrollTop;
                    zemGridController.broadcastEvent(
                        zemGridConstants.events.BODY_VERTICAL_SCROLL,
                        event.target.scrollLeft
                    );
                }
            }

            scope.$watch('rows', function (rows) {
                if (rows) {
                    $timeout(function () {
                        // Calculate columns widths after body rows are rendered
                        var columns = element.querySelectorAll('.zem-grid-cell');
                        columns.each(function (index, column) {
                            var columnWidth = column.offsetWidth;
                            if (scope.columnsWidths[index] < columnWidth) {
                                scope.columnsWidths[index] = columnWidth;
                            }
                        });
                    }, 0, false);
                }
            });

            element.on('scroll', handleScroll);
        },
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
