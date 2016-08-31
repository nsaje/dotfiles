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
            var requestAnimationFrame = zemGridUIService.requestAnimationFrame;
            ctrl.grid.header.ui.element = element;

            function resizeColumns () {
                // Workaround: call resize 2 times - in some cases  (e.g. initialization) table is not
                // yet rendered causing resize to function on empty table. On the other hand call resize
                // immediately to prevent flickering if table is already rendered (e.g. toggling columns)
                zemGridUIService.resizeGridColumns(ctrl.grid);
                $timeout(function () {
                    requestAnimationFrame(function () {
                        zemGridUIService.resizeGridColumns(ctrl.grid);
                    });
                }, 0, false);
            }

            function handleHorizontalScroll () {
                var leftOffset = -1 * ctrl.grid.body.ui.scrollLeft;
                var translateCssProperty = 'translateX(' + leftOffset + 'px)';

                element.css({
                    '-webkit-transform': translateCssProperty,
                    '-moz-transform': translateCssProperty,
                    '-ms-transform': translateCssProperty,
                    'transform': translateCssProperty,
                });
            }

            var scrolling = false;

            var scrollStarted = function () {
                // On start scroll move pivot columns to original position
                scrolling = true;
                zemGridUIService.updatePivotColumns(ctrl.grid, 0);
            };

            var scrollStopped = debounce(function () {
                // Animate fade-in
                // First set position to be hidden on the left side and after that slide-in columns to correct fixed position
                var startPosition = Math.max(0, ctrl.grid.body.ui.scrollLeft - ctrl.grid.ui.pivotColumnsWidth);
                var endPosition = ctrl.grid.body.ui.scrollLeft;
                zemGridUIService.updatePivotColumns(ctrl.grid, startPosition);
                $timeout(function () {
                    zemGridUIService.updatePivotColumns(ctrl.grid, endPosition, true);
                    scrolling = false;
                });
            }, 100);

            function handleHorizontalScrollPivotColumns () {
                if (!scrolling) {
                    scrollStarted();
                } else {
                    scrollStopped();
                }
            }

            // TODO: create util service and move this function there
            function debounce (func, wait, immediate) {
                var timeout;
                return function () {
                    var context = this, args = arguments;
                    var later = function () {
                        timeout = null;
                        if (!immediate) func.apply(context, args);
                    };
                    var callNow = immediate && !timeout;
                    clearTimeout(timeout);
                    timeout = setTimeout(later, wait);
                    if (callNow) func.apply(context, args);
                };
            }

            pubsub.register(pubsub.EVENTS.DATA_UPDATED, scope, resizeColumns);
            pubsub.register(pubsub.EVENTS.EXT_COLUMNS_UPDATED, scope, resizeColumns);
            pubsub.register(pubsub.EVENTS.BODY_HORIZONTAL_SCROLL, scope, handleHorizontalScroll);
            pubsub.register(pubsub.EVENTS.BODY_HORIZONTAL_SCROLL, scope, handleHorizontalScrollPivotColumns);

            // Resize columns on window resize
            window.addEventListener ('resize', resizeColumns);
            scope.$on('$destroy', function () {
                window.removeEventListener ('resize', resizeColumns);
            });

            resizeColumns();
        },
        controller: ['$scope', function ($scope) {
            var vm = this;
            var pubsub = this.grid.meta.pubsub;
            var columnsService = this.grid.meta.columnsService;

            vm.model = {};

            initialize();

            function initialize () {
                initializeColumns();
                pubsub.register(pubsub.EVENTS.EXT_COLUMNS_UPDATED, $scope, initializeColumns);
            }

            function initializeColumns () {
                vm.model.visibleColumns = columnsService.getVisibleColumns();

                // visibleColumns is shared with body to optimize virtual scroll performance
                vm.grid.header.visibleColumns = vm.model.visibleColumns;
            }
        }],
    };
}]);
