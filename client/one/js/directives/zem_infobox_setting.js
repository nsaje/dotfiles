/*global $,angular,constants*/
'use strict';

angular.module('one.legacy').directive('zemInfoboxSetting', function (config, $window) {

    return {
        restrict: 'E',
        scope: {
            label: '=',
            value: '=',
            internal: '=',
            valueDescription: '=',
            valueClass: '=',
            detailsLabel: '=',
            detailsContent: '=',
            warning: '=',
            icon: '=',
            tooltipText: '=',
        },
        templateUrl: '/partials/zem_infobox_setting.html',
        controller: function ($scope, $element, $attrs) {
            $scope.config = config;
            $scope.constants = constants;
            $scope.statusActive = false;

            $scope.isSet = function (val) {
                if (typeof val === 'undefined') {
                    return false;
                }

                return val !== null && val !== undefined;
            };

        }
    };
});
