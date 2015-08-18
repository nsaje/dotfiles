/*global $,oneApp*/
"use strict";

oneApp.directive('zemTutorialPopover', ['$compile', '$timeout', function($compile, $timeout) {
    return {
        restrict: 'A',
        compile: function (tElem, tAttrs) {
            return function (scope, element, attrs) {

                //TODO: add toggle switch to it - show only under certain permission
                element.attr('popover', attrs.zemTutorialPopover);
                element.attr('popover-placement', attrs.zemTutorialPopoverPlacement);
                element.attr('popover-trigger', 'openTutorial');
                element.attr('popover-popup-delay', '500');
                element.attr('popover-append-to-body', 'false');
                element.attr('popover-class', 'tutorial');

                // prevent recursive compilation
                element.removeAttr('zem-tutorial-popover');

                $compile(element)(scope);

                $timeout(function() {
                    element.trigger('openTutorial');
                    // TODO: close when click on popover
                    element.on('click', function(e) {
                        element.trigger('closeTutorial');
                    });
                }, 0);
            };
        }
    };
}]);
