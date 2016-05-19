/* globals oneApp */
'use strict';

oneApp.directive('zemGridFooter', ['$timeout', 'zemGridUIService', function ($timeout, zemGridUIService) {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_footer.html',
        link: function postLink (scope, element) {
            var pubsub = scope.ctrl.grid.meta.pubsub;

            function updateFooter () {
                $timeout(function () {
                    scope.ctrl.grid.ui.state.footerRendered = true;
                    scope.ctrl.grid.footer.element = element;
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

            pubsub.register(pubsub.EVENTS.ROWS_UPDATED, updateFooter);

            pubsub.register(pubsub.EVENTS.BODY_HORIZONTAL_SCROLL, function (event, leftOffset) {
                handleHorizontalScroll(leftOffset);
            });
        },
        controller: [function () {}],
    };
}]);
