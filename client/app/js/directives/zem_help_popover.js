/*global $,oneApp*/
"use strict";

oneApp.directive('zemHelpPopover', function(config) {
    return {
        restrict: 'E',
        scope: {
            content: '@'
        },
        template: '<a href="" class="help-popover" popover="{{ content }}" popover-placement="top" popover-trigger="mouseenter"></a>'
    };
});
