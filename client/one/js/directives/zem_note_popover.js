/*global $,oneApp*/
"use strict";

oneApp.directive('zemNotePopover', function() {
    return {
        restrict: 'E',
        scope: {
            content: '@',
            placement: '@'
        },
        template: '<i ng-if="!!content" class="glyphicon glyphicon-align-justify" zem-lazy-popover-html-unsafe="{{ content }}" zem-lazy-popover-placement="{{ placement }}" zem-lazy-popover-append-to-body="true" zem-lazy-popover-animation-class="fade"></i><span ng-if="!content">N/A</span>'
    };
});
