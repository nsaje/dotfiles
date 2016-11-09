/* globals angular,constants */
'use strict';

angular.module('one.legacy').directive('zemFacebookPage', function ($parse) {
    return {
        restrict: 'E',
        templateUrl: '/partials/zem_facebook_page.html',
        scope: {
            hasPermission: '=zemHasPermission',
            isPermissionInternal: '=zemIsPermissionInternal',
            config: '=zemConfig',
            accountId: '=zemAccountId',
            facebookPageErrors: '=zemFacebookPageErrors',
            facebookPageChanged: '=zemFacebookPageChanged',
            settings: '=zemSettings',
        },
        controller: function ($scope) {
            $scope.constants = constants;

            $scope.onFacebookPageChange = function () {
                $scope.facebookPageChanged = true;
            };

            $scope.clearFacebookPage = function () {
                $scope.settings.facebookPage = null;
                $scope.settings.facebookStatus = constants.facebookStatus.EMPTY;
                $scope.facebookPageChanged = true;
            };
        }
    };
});
