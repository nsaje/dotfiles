/*global $,oneApp*/
"use strict";

oneApp.directive('zemHelpPopover', function() {
    return {
        restrict: 'E',
        scope: {
            content: '@',
            placement: '@'
        },
        template: '<span class="help-popover" popover-html-unsafe="{{ content }}" popover-placement="{{ placement }}" popover-trigger="mouseenter" popover-append-to-body="true"></span>'
    };
});
