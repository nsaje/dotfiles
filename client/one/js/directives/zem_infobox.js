/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemInfobox', ['config', '$window', function(config, $window) {

    return {
        restrict: 'E',
        scope: {
            header: '=',
            settings: '=',
            linkTo: '=',
            elementId: '='
        },
        templateUrl: '/partials/zem_infobox.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.config = config;
        }]
    };

}]);
