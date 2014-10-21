/*global $,oneApp*/
"use strict";

// https://github.com/angular-ui/bootstrap/issues/520
oneApp.directive('popoverHtmlUnsafePopup', [function () {
    return {
        restrict: 'EA',
        replace: true,
        scope: { title: '@', content: '@', placement: '@', animation: '&', isOpen: '&' },
        templateUrl: '/partials/popover_html_unsafe_popup.html'
    };
}]);

oneApp.directive('popoverHtmlUnsafe', [ '$tooltip', function ($tooltip) {
    return $tooltip('popoverHtmlUnsafe', 'popover', 'click');
}]);
