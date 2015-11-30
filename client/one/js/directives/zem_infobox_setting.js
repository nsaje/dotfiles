/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemInfoboxSetting', ['config', '$window', function(config, $window) {

    return {
        restrict: 'E',
        scope: {
            label: '=',
            value: '='
        },
        templateUrl: '/partials/zem_infobox_setting.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {}]
    }

}]);
