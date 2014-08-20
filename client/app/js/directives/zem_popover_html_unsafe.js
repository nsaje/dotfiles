/*global $,oneApp*/
"use strict";

// https://github.com/angular-ui/bootstrap/issues/520
oneApp.directive('popoverHtmlUnsafePopup', ['config', function (config) {
    return {
        restrict: 'EA',
        replace: true,
        scope: { title: '@', content: '@', placement: '@', animation: '&', isOpen: '&' },
        templateUrl: config.static_url + '/partials/popover_html_unsafe_popup.html'
    };
}]);

oneApp.directive('popoverHtmlUnsafe', [ '$tooltip', function ($tooltip) {
    return $tooltip('popoverHtmlUnsafe', 'popover', 'click');
}]);
