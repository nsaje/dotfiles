/*global $,oneApp*/
"use strict";

oneApp.directive('zemSelect2Open', ['$parse', '$rootScope', function($parse, $rootScope) {
    return {
        restrict: 'A',
        compile: function($element, attr) {
            var fn = $parse(attr.zemSelect2Open);
            return function(scope, element) {
                element.on('select2-opening', function(e) {
                    var callback = function() {
                        fn(scope, {$event: e});
                    };
                    scope.$apply(callback);
                });
            }
        }
    };
}]);
