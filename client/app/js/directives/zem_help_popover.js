/*global $,oneApp*/
"use strict";

oneApp.directive('zemHelpPopover', function(config) {
    return {
        restrict: 'E',
        scope: {
            content: '@',
            placement: '@'
        },
        template: '<a href="" class="help-popover" popover="{{ content }}" popover-placement="{{ placement }}" popover-trigger="mouseenter" popover-append-to-body="true"></a>'
    };
});
