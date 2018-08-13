angular.module('one.widgets').directive('zemSettingsTransclude', function() {
    return {
        restrict: 'EAC',
        terminal: true,
        compile: function() {
            return function ngTranscludePostLink(
                $scope,
                $element,
                $attrs,
                controller,
                $transclude
            ) {
                // Bind parent controller to $container variable and transclude to correct slot
                var slotName = $attrs.zemSettingsTransclude;
                $transclude(
                    function(element, scope) {
                        scope.$container = $scope.$ctrl;
                        $element.append(element);
                    },
                    null,
                    slotName
                );
            };
        },
    };
});
