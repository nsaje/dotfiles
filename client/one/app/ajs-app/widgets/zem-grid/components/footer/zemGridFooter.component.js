angular.module('one.widgets').directive('zemGridFooter', function(NgZone) {
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        template: require('./zemGridFooter.component.html'),
        link: function postLink(scope, element) {
            var pubsub = scope.ctrl.grid.meta.pubsub;
            var grid = scope.ctrl.grid;
            grid.footer.ui.element = element;

            initialize();

            function initialize() {
                initializeBodyScrollerSync();
                pubsub.register(
                    pubsub.EVENTS.BODY_HORIZONTAL_SCROLL,
                    scope,
                    function(event, leftOffset) {
                        handleHorizontalScroll(leftOffset);
                    }
                );
            }

            function handleHorizontalScroll(leftOffset) {
                leftOffset = -1 * leftOffset;
                var translateCssProperty = 'translateX(' + leftOffset + 'px)';

                element.find('.zem-grid-footer').css({
                    '-webkit-transform': translateCssProperty,
                    '-ms-transform': translateCssProperty,
                    '-moz-transform': translateCssProperty,
                    transform: translateCssProperty,
                });
            }

            function initializeBodyScrollerSync() {
                // Sticky scroller allows user to use scroll also when footer is sticky (fixed at bottom)
                // To achieve this we sync body scroll with sticky one and show it only when
                // footer is sticky and body scroller is not visible in viewport
                var ignoreNextScroll = false;
                NgZone.runOutsideAngular(function() {
                    element
                        .find('.zem-grid-sticky__scroller-container')
                        .on('scroll', function(event) {
                            if (
                                grid.body.ui.scrollLeft ===
                                event.target.scrollLeft
                            )
                                return;
                            setTimeout(function() {
                                ignoreNextScroll = true;
                                grid.body.ui.element.scrollLeft(
                                    event.target.scrollLeft
                                );
                            }, 0);
                        });
                });
                NgZone.runOutsideAngular(function() {
                    grid.body.ui.element.on('scroll', function(event) {
                        if (ignoreNextScroll) {
                            // Ignore body scroll event that when it was triggered by sticky scroller
                            ignoreNextScroll = false;
                            return;
                        }

                        var scrollContainer = grid.footer.ui.element.find(
                            '.zem-grid-sticky__scroller-container'
                        );
                        scrollContainer.scrollLeft(event.target.scrollLeft);
                    });
                });
            }
        },
        controller: function() {},
    };
});
