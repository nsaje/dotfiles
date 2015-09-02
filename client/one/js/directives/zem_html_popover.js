/*global $,oneApp*/
"use strict";

oneApp.directive('zemHtmlPopover', ['$http', '$templateCache', '$compile', '$parse', '$timeout', function($http, $templateCache, $compile, $parse, $timeout) {
    // zem-html-popover = path to template
    // popover-updater = scope item to watch (optional)

    return {
        restrict: 'A',
        scope: true,
        compile: function (tElem, tAttrs) {
            if (!tElem.attr('popover-html-unsafe')) {
                tElem.attr('popover-html-unsafe', '{{popover}}');
            }
            return function (scope, element, attrs) {
                var templateUrl = $parse(attrs.zemHtmlPopover)(scope);
                scope.popover = " ";

                function loadTemplate() {
                    $http.get(templateUrl, {cache: $templateCache })
                        .success(function (content) {
                            var container = $('<div/>');
                            container.html($compile(content.trim())(scope));
                            $timeout(function () {
                                scope.popover = container.html();
                            });
                        });
                }

                element.removeAttr('zem-html-popover');
                $compile(element)(scope);

                if (angular.isDefined(attrs.popoverUpdater)) {
                    var unwatch_function = null
                    // We only start watching on first mouseenter
                    element.on("mouseenter", function () {
                        loadTemplate();
                        if (!unwatch_function) {
                            unwatch_function = scope.$watch(attrs.popoverUpdater, function () {
                                loadTemplate();
                            });
                        }
                    });
                    element.on("mouseleave", function() {
                        unwatch_function();
                        unwatch_function = null;
                    });
                } else {
                    element.on("mouseenter", loadTemplate);
                }
            };
        }
    };
}]);
