/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemInfoboxSetting', ['config', '$window', function(config, $window) {

    return {
        restrict: 'E',
        scope: {
            label: '=',
            value: '=',
            valueDescription: '=',
            detailsVisible: '=',
            detailsLabel: '=',
            detailsContent: '=',
            statusActive: '=',
            tooltip: '=',
            icon: '='
        },
        templateUrl: '/partials/zem_infobox_setting.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
        
            $scope.icon = "happy";
            $scope.detailsVisible = false;
            $scope.detailsLabel = "Kick me";
            $scope.detailsContent = "BAM";
            $scope.tooltip = "Test"
            $scope.statusActive = false;

            $scope.isSet = function (val) {
                if (typeof val === "undefined") {
                    return false;
                }

                return val !== null;
            };

            $scope.showDetails = function () {
                $scope.detailsVisible = true;
            };

            $scope.hideDetails = function () {
                $scope.detailsVisible = false;
            };
        
        }]
    }

}]);
