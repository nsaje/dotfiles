/*global $,oneApp*/
"use strict";

oneApp.directive('zemLazyPopover', ['$http', '$templateCache', '$compile', '$parse', '$timeout', '$position', '$document', function($http, $templateCache, $compile, $parse, $timeout, $position, $document) {
    // zem-lazy-popover = path to template
    // zem-lazy-popover-placement = top/bottom/left/right
    // popover-updater = scope item to watch (optional)

    return {
        restrict: 'A',
        scope: false,
//        transclude: true,
        compile: function (tElem, tAttrs) {
            return function (scope, element, attrs) {
                var appendToBody = false;
                var ttScope = null;
                var tooltip = null;
                var positionTooltip = function () {
                  if (!tooltip) { return; }

                  var ttPosition = $position.positionElements(element, tooltip, ttScope.placement, ttScope.appendToBody);
                  ttPosition.top += 'px';
                  ttPosition.left += 'px';

                  // Now set the calculated positioning.
                  tooltip.css( ttPosition );
                };
                element.on("mouseleave", function() {
                    if (tooltip) {
                        tooltip.remove();
                        tooltip = null;
                    }
                    if (ttScope) {
                        ttScope.$destroy();
                        ttScope = null;
                    }
                });
                element.on("mouseenter", function() {
                    if (tooltip) {
                        return
                    }
                    var templateUrl = attrs.zemLazyPopover;
                    console.log("TU", templateUrl);
                    $http.get(templateUrl, {cache: $templateCache })
                        .success(function (content) {
                            ttScope = scope.$new(false);
                            ttScope.placement = angular.isDefined(attrs.zemLazyPopoverPlacement) ? attrs.zemLazyPopoverPlacement : "";
                            ttScope.appendToBody = angular.isDefined(attrs.zemLazyPopoverAppendToBody) ? scope.$parent.$eval(attrs.zemLazyPopoverAppendToBody) : false;
//                            console.log(content);
                            tooltip = $compile(content)(ttScope, function (tooltip) {
                                // Place it somewhere out of view, so we can render & get the size first
                                tooltip.css({ top: -5000, left: 0, display: 'block' });
                                if (ttScope.appendToBody) {
                                    $document.find( 'body' ).append( tooltip );
                                } else {
                                    element.after( tooltip );
                                }
                                $timeout(function () {
//                                  console.log(tooltip);
//                                  console.log(tooltip[0].outerHTML);
                                  positionTooltip();
                                });
                            });
                            

                        
                        });
                    
                });
                
                
            };
        }
    };
}]);
