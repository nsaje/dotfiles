/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridFooter', ['$timeout', 'config', 'zemGridConstants', function ($timeout, config, zemGridConstants) {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
            pubsub: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_footer.html',
        link: function postLink (scope, element) {
            var pubsub = scope.ctrl.pubsub;

            scope.$watch('ctrl.grid.footer', function (footer) {
                if (footer) {
                    $timeout(function () {
                        // Calculate columns widths after footer is rendered
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

            pubsub.register(pubsub.EVENTS.BODY_HORIZONTAL_SCROLL, function (event, value) {
                var leftOffset = -1 * value;
                var translateCssProperty = 'translateX(' + leftOffset + 'px)';

                element.css({
                    '-webkit-transform': translateCssProperty,
                    '-ms-transform': translateCssProperty,
                    'transform': translateCssProperty,
                });
            });
        },
        controller: [function () {
            this.getCellStyle = function (index) {
                var width = 'auto';
                if (this.grid.ui.columnWidths[index]) {
                    width = this.grid.ui.columnWidths[index] + 'px';
                }
                return {'min-width': width};
            };
        }],
    };
}]);
