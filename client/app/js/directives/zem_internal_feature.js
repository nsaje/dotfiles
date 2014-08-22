/*global $,oneApp*/
"use strict";

oneApp.directive('zemInternalFeature', function(config) {
    return {
        restrict: 'E',
        scope: {
            popoverPlacement: '@'    
        },
        template: '<a href="" popover="The green triangle marks parts of the user interface that are only seen by sales and account managers." popover-placement="{{popoverPlacement || \'top\'}}" popover-trigger="mouseenter" popover-append-to-body="true" class="internal"></a>'
    };
});
