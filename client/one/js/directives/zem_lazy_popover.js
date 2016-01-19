/*global $,oneApp*/
"use strict";

$zemLazyPopoverDirective.$inject = ['$http', '$templateCache', '$compile', '$parse', '$timeout', '$position', '$document'];
function $zemLazyPopoverDirective($http, $templateCache, $compile, $parse, $timeout, $position, $document) {
    // zem-lazy-popover-template = path to template (evaluated)
    // zem-lazy-popover-text = text content (safe by default, evaulated)
    // zem-lazy-popover-html-unsafe = html (evaluated)

    // zem-lazy-popover-placement = top/bottom/left/right
    // zem-lazy-popover-animation-class = fade
    // zem-lazy-popover-append-to-body = true/false
    // zem-lazy-popover-event = mouseleave/click (mouseleave by default)
    
    var entityMap = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
    };

    function sanitizeString(str) {
        return String(str).replace(/[&<>]/g, function (s) {
            return entityMap[s];
        });    
    }
    
    // We have a global one-popup policy, so here's the previous one to close
    var closeExisting = null;
    var transitionTimeout = null;
    return {
        restrict: 'A',
        link: function (scope, element, attrs) {
            var appendToBody = false;
            var ttScope = null;
            var tooltip = null;
            var event = attrs.zemLazyPopoverEvent || "mouseleave";

            var positionTooltip = function () {
                if (!tooltip) { return; }
                var ttPosition = $position.positionElements(element, tooltip, ttScope.placement, ttScope.appendToBody);
                ttPosition.top += 'px';
                ttPosition.left += 'px';
                // Now set the calculated positioning.
                tooltip.css( ttPosition );
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
            
            var hide = function() {
                // This function hides the tooltip
                // it's implemented by removing the tooltip entirely from DOM and angular
                // Add fade commands
                if (tooltip) {
                    tooltip.removeClass("in");
                    tooltip.addClass("out");
                }

                
                // Last thing before destorying the scope is removing the 
                        
                if (ttScope) {
                    // If there's fadeout or similar animation, wait a bit with removal
                    if (ttScope.animationClass) {
                        // If transition-out has already been initiated, we are on the way out anyway
                        if ( !transitionTimeout ) {
                           // We save the function for closing the current tooltip, so if we're displaying a different one we can close it earlier han timeout
                           transitionTimeout = $timeout(removeTooltip, 500);
                        }
                    } else {
                        removeTooltip();
                    }
                };
                element.off(event, hide);
            };

            element.on('$destroy', hide);
            
            element.on("mouseenter", function() {
                // If we have a timeout set, cancel it and add in classes
                if ( transitionTimeout ) {
                    $timeout.cancel( transitionTimeout );
                    transitionTimeout = null;
                }                                    // If there's any other popup active, close it immediately   
                if (closeExisting) {
                  closeExisting();
                }
                closeExisting = removeTooltip;
 
                // If the scope already exists, do nothing
                if (ttScope) {
                    return
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

                element.on(event, hide);

                function haveTemplateContent(templateContent) {
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
                                  templateContent + 
                                  '</div>' +
                                  '</div>' +
                                  '</div>';
                                  
                    tooltip = $compile(content)(ttScope, function (tooltipNew) {
                        // Place it somewhere out of the view, so we can render & get the size first
                        tooltipNew.css({ top: -5000, left: 0, display: 'block' });
                        if (ttScope.appendToBody) {
                            $document.find( 'body' ).append( tooltipNew );
                        } else {
                            element.after( tooltipNew );
                        }
                    });

                    $timeout(function () {
                        // By the time we reach this, we might have already moved the mouse away
                        if (tooltip) {
                            tooltip.addClass("in");
                            positionTooltip();                                  
                        }
                    
                        if (ttScope) {
                            ttScope.$watch(positionTooltip, 0, false);
                        }

                    });
                }

                if (templateUrl) {
                    $http.get(templateUrl, {cache: $templateCache })
                        .success(haveTemplateContent);
                } else if (templateHtml) {
                    haveTemplateContent(templateHtml);
                } else {
                    // Should an error be thrown?
                }
                
                ttScope.$apply();

            });
        }
    };
};

angular.module('one')
  .directive('zemLazyPopoverTemplate', $zemLazyPopoverDirective)
  .directive('zemLazyPopoverText', $zemLazyPopoverDirective)
  .directive('zemLazyPopoverHtmlUnsafe', $zemLazyPopoverDirective);

