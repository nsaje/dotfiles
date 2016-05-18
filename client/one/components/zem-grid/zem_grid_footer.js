/* globals oneApp, angular */
'use strict';

oneApp.directive('zemGridFooter', ['$timeout', 'zemGridUIService', function ($timeout, zemGridUIService) {

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
            scope.ctrl.grid.footer.element = element;

            var pubsub = scope.ctrl.pubsub;

            scope.$watch('ctrl.grid.footer', function (footer) {
                if (footer) {
                    $timeout(function () {
                        scope.ctrl.grid.ui.state.footerRendered = true;
                        scope.ctrl.grid.footer.element = element;

                        zemGridUIService.resizeGridColumns(scope.ctrl.grid);
                    }, 0, false);
                }
            });

            // pubsub.register(pubsub.EVENTS.ROWS_UPDATED, function () {
            //     $timeout(function () {
            //         scope.ctrl.grid.ui.state.footerRendered = true;
            //         scope.ctrl.grid.footer.element = element;
            //         zemGridUIService.resizeGridColumns(scope.ctrl.grid);
            //     }, 0, false);
            // });

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
        controller: ['zemGridService', function (zemGridService) {
            this.getCellStyle = function (index) {
                return zemGridService.getCellStyle(this.grid, index);
            };
        }],
    };
}]);
