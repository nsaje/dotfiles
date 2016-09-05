/*global $,angular,constants*/
'use strict';

angular.module('one.legacy').directive('zemInfobox', ['config', '$window', function (config, $window) {

    return {
        restrict: 'E',
        scope: {
            header: '=',
            basicSettings: '=',
            performanceSettings: '=',
            linkTo: '=',
            stateId: '='
        },
        templateUrl: '/partials/zem_infobox.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.config = config;
            $scope.constants = constants;
        }]
    };

}]);
