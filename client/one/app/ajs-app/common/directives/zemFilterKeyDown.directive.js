var commonHelpers = require('../../../shared/helpers/common.helpers');

angular.module('one.common').directive('zemFilterKeyDown', function() {
    return {
        restrict: 'A',
        link: function(scope, element, attrs) {
            element.bind('keydown', function($event) {
                var filter = [].concat(
                    commonHelpers.getValueOrDefault(
                        scope.$apply(attrs.zemFilterKeyDown),
                        []
                    )
                );
                var keyCode = $event.keyCode || $event.which;
                if (filter.indexOf(keyCode) !== -1) {
                    $event.preventDefault();
                }
            });
        },
    };
});
