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

            function updatePivotColumns () {
                //zemGridUIService.updatePivotColumns(ctrl.grid); - Temporary shut down pivot columns (problem on OSx)
            }

            pubsub.register(pubsub.EVENTS.DATA_UPDATED, scope, resizeColumns);
            pubsub.register(pubsub.EVENTS.EXT_COLUMNS_UPDATED, scope, resizeColumns);
            pubsub.register(pubsub.EVENTS.BODY_HORIZONTAL_SCROLL, scope, handleHorizontalScroll);
            pubsub.register(pubsub.EVENTS.BODY_HORIZONTAL_SCROLL, scope, updatePivotColumns);

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
