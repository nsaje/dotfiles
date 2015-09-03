/*global $,oneApp*/
"use strict";

oneApp.directive('zemLazyPopover', ['$http', '$templateCache', '$compile', '$parse', '$timeout', '$position', '$document', function($http, $templateCache, $compile, $parse, $timeout, $position, $document) {
    // zem-lazy-popover = path to template
    // zem-lazy-popover-placement = top/bottom/left/right

    return {
        restrict: 'A',
   //        transclude: true,
        compile: function (tElem, tAttrs) {
            return function (scope, element, attrs) {
                var appendToBody = false;
                var ttScope = null;
                var tooltip = null;
                var transitionTimeout;

                var positionTooltip = function () {
                  if (!tooltip) { return; }
                  var ttPosition = $position.positionElements(element, tooltip, ttScope.placement, ttScope.appendToBody);
                  ttPosition.top += 'px';
                  ttPosition.left += 'px';
                  // Now set the calculated positioning.
                  tooltip.css( ttPosition );
                };

                var hide = function() {
                    // This function hides the tooltip
                    // it's implemented by removing the tooltip entirely from DOM and angular
                    // Add fade commands
                    if (tooltip) {
                        tooltip.removeClass("in");
                        tooltip.addClass("out");
                    }

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
                    // Last thing before destorying the scope is removing the 
                    if (ttScope) {
                        ttScope.$on("$destroy", function () {
                          element.off("mouseleave", hide);
                        });
                        // If there's fadeout or similar animation, wait a bit with removal
                        if (ttScope.animationClass) {
                            // If transition-out has already been initiated, we are on the way out anyway
                            if ( !transitionTimeout ) {
                               transitionTimeout = $timeout(removeTooltip, 500);
                            }
                        } else {
                            removeTooltip();
                        }
                    }


                };

                
                element.on("mouseenter", function() {
                    // If we have a timeout set, cancel it and add in classes
                    if ( transitionTimeout ) {
                        $timeout.cancel( transitionTimeout );
                        transitionTimeout = null;
                        if (tooltip) {
                            tooltip.removeClass("out");
                            tooltip.addClass("in");
                        }
                    }
                    // If the scope already exists, do nothing
                    if (ttScope) {
                        return
                    }
                    ttScope = scope.$new(false);

                    element.on("mouseleave", hide);
                    scope.$on("$destroy", hide);


                    var templateUrl = $parse(attrs.zemLazyPopover)(scope);
                    
                    $http.get(templateUrl, {cache: $templateCache })
                        .success(function (template_content) {
                            if (!ttScope) {
                                // Mouseleave might have happened already
                                return;
                            }
                            ttScope.placement = angular.isDefined(attrs.zemLazyPopoverPlacement) ? attrs.zemLazyPopoverPlacement : "";
                            ttScope.appendToBody = angular.isDefined(attrs.zemLazyPopoverAppendToBody) ? scope.$parent.$eval(attrs.zemLazyPopoverAppendToBody) : false;
                            ttScope.animationClass = angular.isDefined(attrs.zemLazyPopoverAnimationClass) ? attrs.zemLazyPopoverAnimationClass : false;
                            var content = '<div class="popover {{ placement }} {{animationClass }}">' +
                                          '<div class="arrow"></div>' + 
                                          '<div class="popover-inner">' +
                                          '<div class="popover-content">' +
                                          template_content + 
                                          '</div>' +
                                          '</div>' +
                                          '</div>'

                            $compile(content)(ttScope, function (tooltip_new) {
                                tooltip = tooltip_new;
                                // Place it somewhere out of the view, so we can render & get the size first
                                tooltip.css({ top: -5000, left: 0, display: 'block' });
                                if (ttScope.appendToBody) {
                                    $document.find( 'body' ).append( tooltip );
                                } else {
                                    element.after( tooltip );
                                }
                                $timeout(function () {
                                    // By the time we reach this, we might have already moved the mouse away

                                    if (tooltip) {
                                        tooltip.addClass("in");
                                        positionTooltip();
                                    }
                                    ttScope.$watch(function () {
                                        $timeout(positionTooltip, 0, false);
                                    });

                                });
                            });
                        
                        });
                });
            };
        }
    };
}]);
