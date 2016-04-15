/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridHeader', ['$timeout', 'config', 'zemGridConstants', function ($timeout, config, zemGridConstants) {

    return {
        restrict: 'E',
        replace: true,
        scope: true,
        controllerAs: 'ctrl',
        bindToController: {
            options: '=',
            header: '=',
            columnsWidths: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_header.html',
        link: function postLink (scope, element) {
            scope.$watch('header', function (header) {
                if (header) {
                    $timeout(function () {
                        // Calculate columns widths after header is rendered
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

            scope.$on(zemGridConstants.events.BODY_HORIZONTAL_SCROLL, function (event, value) {
                var leftOffset = -1 * value;
                var translateCssProperty = 'translateX(' + leftOffset + 'px)';

                element.css({
                    '-webkit-transform': translateCssProperty,
                    '-ms-transform': translateCssProperty,
                    'transform': translateCssProperty,
                });
            });
        },
        controller: ['$scope', function ($scope) {
            $scope.getCellStyle = function (index) {
                var width = 'auto';
                if ($scope.columnsWidths[index]) {
                    width = $scope.columnsWidths[index] + 'px';
                }
                return {'min-width': width};
            };
        }],
    };
}]);
