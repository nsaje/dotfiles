/*global $,oneApp,constants*/
'use strict';

oneApp.directive('zemInfoboxSetting', ['config', '$window', function (config, $window) {

    return {
        restrict: 'E',
        scope: {
            label: '=',
            value: '=',
            internal: '=',
            valueDescription: '=',
            valueClass: '=',
            detailsLabel: '=',
            detailsHideLabel: '=',
            detailsContent: '=',
            warning: '=',
            icon: '=',
            tooltipText: '=',
        },
        templateUrl: '/partials/zem_infobox_setting.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
            $scope.config = config;
            $scope.constants = constants;
            $scope.detailsVisible = false;
            $scope.statusActive = false;

            $scope.isSet = function (val) {
                if (typeof val === 'undefined') {
                    return false;
                }

                return val !== null && val !== undefined;
            };

            $scope.showDetails = function () {
                $scope.detailsVisible = true;
            };

            $scope.hideDetails = function () {
                $scope.detailsVisible = false;
            };

        }]
    };
}]);
