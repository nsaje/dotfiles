/*global $,oneApp*/
'use strict';

oneApp.directive('zemInternalFeature', function () {
    return {
        restrict: 'E',
        scope: {
            popoverPlacement: '@'
        },
        template: '<a href="" zem-lazy-popover-text="The green triangle marks parts of the user interface that are only seen by sales and account managers." zem-lazy-popover-placement="{{popoverPlacement || \'top\'}}" zem-lazy-popover-append-to-body="true" zem-lazy-popover-animation-class="fade" class="internal"></a>'
    };
});
