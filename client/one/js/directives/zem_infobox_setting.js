/*global $,oneApp,constants*/
"use strict";

oneApp.directive('zemInfoboxSetting', ['config', '$window', function(config, $window) {

    return {
        restrict: 'E',
        scope: {
            label: '=',
            value: '=',
            detailsVisible: '=',
            detailsLabel: '=',
            detailsContent: '=',
            icon: '='
        },
        templateUrl: '/partials/zem_infobox_setting.html',
        controller: ['$scope', '$element', '$attrs', function ($scope, $element, $attrs) {
        
            $scope.icon = null;
            $scope.detailsVisible = false;
            $scope.detailsLabel = null;
            $scope.detailsContent = null;

            $scope.isSet = function (val) {
                if (typeof val === "undefined") {
                    return false;
                }

                return val !== null;
            };
        
        }]
    }

}]);
