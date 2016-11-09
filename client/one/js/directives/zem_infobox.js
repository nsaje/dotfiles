/*global $,angular,constants*/
'use strict';

angular.module('one.legacy').directive('zemInfobox', function (config, $window) {

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
        controller: function ($scope, $element, $attrs) {
            $scope.config = config;
            $scope.constants = constants;
        }
    };

});
