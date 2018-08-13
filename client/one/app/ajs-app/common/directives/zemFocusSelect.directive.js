angular.module('one.common').directive('zemFocusSelect', function($window) {
    return {
        restrict: 'A',
        link: function(scope, element) {
            $window.setTimeout(function() {
                element[0].focus();
                element[0].setSelectionRange(0, element[0].value.length);
            }, 100);
        },
    };
});
