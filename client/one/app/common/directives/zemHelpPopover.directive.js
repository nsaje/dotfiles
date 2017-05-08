/*global $,angular*/
'use strict';

angular.module('one.common').directive('zemHelpPopover', function () {
    return {
        restrict: 'E',
        scope: {
            content: '@',
            placement: '@'
        },
        template: '<span class="help-popover" ' +
                    'zem-lazy-popover-html-unsafe="{{ content }}"' +
                    'zem-lazy-popover-placement="{{ placement }}"' +
                    'zem-lazy-popover-append-to-body="true"' +
                    'zem-lazy-popover-animation-class="fade">' +
                  '</span>'
    };
});
