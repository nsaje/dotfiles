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
                var unwatch_function = null
                var skipme = 0
                var compiled = null
                compiled = $compile(element);

                function loadTemplate() {
                    var to_run = compiled;
                   compiled(scope);
//                    compiled = $compile(element)(scope);
                    if (!to_run) { 
                            $timeout(function () {
                        compiled.triggerHandler('mouseenter');
                        });
                    }
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

                if (angular.isDefined(attrs.popoverUpdater)) {
                    // We only start watching on first mouseenter
                    element.on("mouseenter", function () {
                        loadTemplate();
                        if (!unwatch_function) {
                            unwatch_function = scope.$watch(attrs.popoverUpdater, function () {
                                loadTemplate();
                            });
                        }
                    });
                    /*element.on("mouseleave", function() {
                        unwatch_function();
                        unwatch_function = null;
                    });*/
                } else {
                    unwatch_function = element.on("mouseenter", loadTemplate);

                    element.on("mouseleave", function() {scope.popover = null; });
                }
            };
        }
    };
}]);
