/*global $,oneApp,constants*/
'use strict';

oneApp.directive('zemInfoboxSetting', ['config', '$window', function (config, $window) {

    return {
        restrict: 'E',
        scope: {
            label: '=',
            value: '=',
            valueDescription: '=',
            detailsVisible: '=',
            detailsLabel: '=',
            detailsHideLabel: '=',
            detailsContent: '=',
            statusActive: '=',
            tooltipText: '=',
            icon: '=',
            warning: '='
        },
        templateUrl: '/partials/zem_infobox_setting.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {

            $scope.config = config;
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
