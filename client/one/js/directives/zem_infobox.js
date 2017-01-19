/*global $,angular,constants*/
'use strict';

angular.module('one.legacy').directive('zemLegacyInfobox', function (config, $window) {

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
        controller: function ($scope, zemSettingsService, zemPermissions) {
            $scope.config = config;
            $scope.constants = constants;
            $scope.hasPermission = zemPermissions.hasPermission;
            $scope.isPermissionInternal = zemPermissions.isPermissionInternal;

            $scope.showNewSettings = function () {
                zemSettingsService.open();
            };
        }
    };

});
