/* globals oneApp,constants */
'use strict';

oneApp.directive('zemFacebookPage', ['$parse', function ($parse) {
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
        controller: ['$scope', function ($scope) {
            $scope.constants = constants;

            $scope.onFacebookPageChange = function () {
                $scope.facebookPageChanged = true;
            };

            $scope.clearFacebookPage = function () {
                $scope.settings.facebookPage = null;
                $scope.settings.facebookStatus = constants.facebookStatus.EMPTY;
                $scope.facebookPageChanged = true;
            };
        }]
    };
}]);
