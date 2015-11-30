/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemInfobox', ['config', '$window', function(config, $window) {

    return {
        restrict: 'E',
        scope: {},
        templateUrl: '/partials/zem_infobox.html'
    };

}]);
