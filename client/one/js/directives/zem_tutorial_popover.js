/*global $,oneApp*/
"use strict";

oneApp.directive('zemTutorialPopover', ['$compile', '$timeout', function($compile, $timeout) {
    return {
        restrict: 'A',
        compile: function (tElem, tAttrs) {
            return function (scope, element, attrs) {
                var ngClick = attrs.ngClick,
                    condition = attrs.zemTutorialPopoverConditionPromise,
                    openPopover = function () {
                        element.trigger('openTutorial');
                        element.on('click', function(e) {
                            element.trigger('closeTutorial');
                        });
                        element.parent().on('click', '.popover', function (e) {
                            element.trigger('closeTutorial');
                        });
                    };

                if (!scope.user.showOnboardingGuidance) { return; }
                
                element.attr('popover', attrs.zemTutorialPopover);
                element.attr('popover-placement', attrs.zemTutorialPopoverPlacement);
                element.attr('popover-trigger', 'openTutorial');
                element.attr('popover-popup-delay', '500');
                element.attr('popover-append-to-body', 'false');
                element.attr('popover-class', attrs.zemTutorialPopoverType || 'tutorial');

                // prevent recursive compilation
                element.removeAttr('zem-tutorial-popover');
                element.removeAttr('ng-click');

                $compile(element)(scope);

                element.attr('ng-click', ngClick);

                $timeout(function () {
                    if (condition) {
                        scope.$eval(condition).then(function (promisedCondition) {
                            if (promisedCondition) { openPopover(); }
                        });
                    } else {
                        openPopover();
                    }
                }, 0);

            };
        }
    };
}]);
