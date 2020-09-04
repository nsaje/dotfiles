$zemLazyPopoverDirective.$inject = [
    '$http',
    '$templateCache',
    '$compile',
    '$parse',
    '$timeout',
    '$uibPosition',
    '$document',
]; // eslint-disable-line max-len
function $zemLazyPopoverDirective(
    $http,
    $templateCache,
    $compile,
    $parse,
    $timeout,
    $position,
    $document
) {
    // zem-lazy-popover-template = path to template (evaluated)
    // zem-lazy-popover-text = text content (safe by default, evaulated)
    // zem-lazy-popover-html-unsafe = html (evaluated)

    // zem-lazy-popover-placement = top/bottom/left/right
    // zem-lazy-popover-animation-class = fade
    // zem-lazy-popover-append-to-body = true/false
    // zem-lazy-popover-event = mouseleave/click (mouseleave by default)

    var entityMap = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
    };

    function sanitizeString(str) {
        return String(str).replace(/[&<>]/g, function(s) {
            return entityMap[s];
        });
    }

    // We have a global one-popup policy, so here's the previous one to close
    var closeExisting = null;
    var transitionTimeout = null;
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            var ttScope = null;
            var tooltip = null;
            var event = attrs.zemLazyPopoverEvent || 'mouseleave';
            var stayOpenOnHover = attrs.zemLazyPopoverStayOpenOnHover || false;

            // eslint-disable-next-line complexity
            var positionTooltip = function() {
                if (!tooltip) {
                    return;
                }

                var ttPosition = $position.positionElements(
                    element,
                    tooltip,
                    ttScope.placement,
                    ttScope.appendToBody
                );

                var windowHeight = document.documentElement.clientHeight;
                var availableSpace = windowHeight - Math.max(0, ttPosition.top);
                var tooltipHeight = tooltip.height();

                var arrow = tooltip.find('.arrow');
                var tooltipContent = tooltip.find('.popover-content');

                if (ttPosition.left < 0) {
                    arrow.css(
                        'transform',
                        'translateX(' + ttPosition.left + 'px)'
                    );
                    ttPosition.left = 0;
                }

                var shift = 0;
                var isTopProblem = ttPosition.top < 0;
                var isSpaceProblem = availableSpace < tooltipHeight;

                if (isSpaceProblem) {
                    shift = tooltipHeight - availableSpace;
                    if (
                        ttScope.placement === 'left' ||
                        ttScope.placement === 'right'
                    ) {
                        arrow.css({top: tooltipHeight / 2 + shift});
                    }
                    if (ttPosition.top - shift < 0) {
                        tooltipContent.css({'max-height': windowHeight});
                        ttPosition.top = 0;
                    } else {
                        ttPosition.top = ttPosition.top - shift;
                    }
                } else if (isTopProblem) {
                    shift = Math.abs(ttPosition.top);
                    if (
                        ttScope.placement === 'left' ||
                        ttScope.placement === 'right'
                    ) {
                        arrow.css({top: tooltipHeight / 2 - shift});
                    }
                    ttPosition.top = 0;
                }

                ttPosition.top += 'px';
                ttPosition.left += 'px';

                // Now set the calculated positioning.
                tooltip.css(ttPosition);
            };

            function removeTooltip() {
                transitionTimeout = null;
                if (tooltip) {
                    tooltip.remove();
                    tooltip = null;
                }
                if (ttScope) {
                    ttScope.$destroy();
                    ttScope = null;
                }
            }

            var hideIfPopoverNotOpenOnHover = function() {
                if (stayOpenOnHover && tooltip && tooltip.is(':hover')) {
                    // In case we want popovers to stay open when hovering over them, we will hide them when mouse
                    // leaves the popover
                    tooltip.on('mouseleave', hide);
                } else {
                    // Otherwise hide the popover immediately
                    hide();
                }
            };

            var hide = function() {
                // This function hides the tooltip
                // it's implemented by removing the tooltip entirely from DOM and angular

                // Add fade commands
                if (tooltip) {
                    tooltip.removeClass('in');
                    tooltip.addClass('out');
                    tooltip.off('mouseleave', hide);
                }

                // Last thing before destorying the scope is removing the
                if (ttScope) {
                    // If there's fadeout or similar animation, wait a bit with removal
                    if (ttScope.animationClass) {
                        // If transition-out has already been initiated, we are on the way out anyway
                        if (!transitionTimeout) {
                            // We save the function for closing the current tooltip, so if we're displaying a
                            // different one we can close it earlier than timeout
                            transitionTimeout = $timeout(removeTooltip, 500);
                        }
                    } else {
                        removeTooltip();
                    }
                }

                element.off(event, hideIfPopoverNotOpenOnHover);
            };

            element.on('$destroy', hide);

            // prettier-ignore
            element.on('mouseenter', function() { // eslint-disable-line complexity
                // If we have a timeout set, cancel it and add in classes
                if (transitionTimeout) {
                    $timeout.cancel(transitionTimeout);
                    transitionTimeout = null;
                }
                // If there's any other popup active, close it immediately
                if (closeExisting) {
                    closeExisting();
                }
                closeExisting = removeTooltip;

                // If the scope already exists, do nothing
                if (ttScope) {
                    return;
                }
                // Before we start creating a new popup, check if there's any content
                var templateUrl, templateHtml;
                if (angular.isDefined(attrs.zemLazyPopoverTemplate)) {
                    templateUrl = $parse(attrs.zemLazyPopoverTemplate)(scope);
                }
                if (angular.isDefined(attrs.zemLazyPopoverHtmlUnsafe)) {
                    templateHtml = attrs.zemLazyPopoverHtmlUnsafe;
                }
                if (angular.isDefined(attrs.zemLazyPopoverText)) {
                    templateHtml = sanitizeString(attrs.zemLazyPopoverText);
                }
                if (!templateUrl && !templateHtml) {
                    // There is no content to be shown
                    return;
                }

                ttScope = scope.$new(false);

                element.on(event, hideIfPopoverNotOpenOnHover);

                function haveTemplateContent(templateContent) {
                    if (!ttScope) {
                        // Mouseleave might have happened already
                        return;
                    }
                    ttScope.placement = angular.isDefined(
                        attrs.zemLazyPopoverPlacement
                    )
                        ? attrs.zemLazyPopoverPlacement
                        : '';
                    ttScope.appendToBody = angular.isDefined(
                        attrs.zemLazyPopoverAppendToBody
                    )
                        ? scope.$parent.$eval(attrs.zemLazyPopoverAppendToBody)
                        : false;
                    ttScope.animationClass = angular.isDefined(
                        attrs.zemLazyPopoverAnimationClass
                    )
                        ? attrs.zemLazyPopoverAnimationClass
                        : false;
                    ttScope.customClasses = angular.isDefined(
                        attrs.zemLazyPopoverCustomClasses
                    )
                        ? attrs.zemLazyPopoverCustomClasses
                        : false;
                    var content =
                        '<div class="popover {{ placement }} {{ animationClass }} {{ customClasses }}">' +
                        '<div class="arrow"></div>' +
                        '<div class="popover-inner">' +
                        '<div class="popover-content custom-scroller">' +
                        templateContent +
                        '</div>' +
                        '</div>' +
                        '</div>';

                    tooltip = $compile(content)(ttScope, function(tooltipNew) {
                        // Place it somewhere out of the view, so we can render & get the size first
                        tooltipNew.css({top: -5000, left: 0, display: 'block'});
                        if (ttScope.appendToBody) {
                            $document.find('body').append(tooltipNew);
                        } else {
                            element.after(tooltipNew);
                        }
                    });

                    $timeout(function() {
                        // By the time we reach this, we might have already moved the mouse away
                        if (tooltip) {
                            tooltip.addClass('in');
                            positionTooltip();
                        }

                        if (ttScope) {
                            ttScope.$watch(positionTooltip, 0, false);
                        }
                    });
                }

                if (templateUrl) {
                    $http
                        .get(templateUrl, {cache: $templateCache})
                        .success(haveTemplateContent);
                } else if (templateHtml) {
                    haveTemplateContent(templateHtml);
                } else {
                    // Should an error be thrown?
                }

                ttScope.$apply();
            });
        },
    };
}

angular
    .module('one')
    .directive('zemLazyPopoverTemplate', $zemLazyPopoverDirective)
    .directive('zemLazyPopoverText', $zemLazyPopoverDirective)
    .directive('zemLazyPopoverHtmlUnsafe', $zemLazyPopoverDirective);
