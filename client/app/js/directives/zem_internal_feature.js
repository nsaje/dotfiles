/*global $,oneApp*/
"use strict";

oneApp.directive('zemInternalFeature', function(config) {
    return {
        restrict: 'E',
        scope: {},
        template: '<a href="" popover="The green triangle marks parts of the user interface that are only seen by sales and account managers." popover-placement="top" popover-trigger="mouseenter" popover-append-to-body="true"><div class="internal"></div></a>'
    };
});
