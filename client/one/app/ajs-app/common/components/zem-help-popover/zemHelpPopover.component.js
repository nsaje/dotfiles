angular.module('one.common').component('zemHelpPopover', {
    bindings: {
        content: '@',
        placement: '@'
    },
    template: '<span class="help-popover" ' +
                'zem-lazy-popover-html-unsafe="{{ $ctrl.content }}"' +
                'zem-lazy-popover-placement="{{ $ctrl.placement }}"' +
                'zem-lazy-popover-append-to-body="true"' +
                'zem-lazy-popover-animation-class="fade">' +
                '</span>'
});
