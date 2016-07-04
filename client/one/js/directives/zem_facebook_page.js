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
            facebookPage: '=zemFacebookPage',
            facebookStatus: '=zemFacebookStatus',
            facebookPageErrors: '=zemFacebookPageErrors',
            facebookPageChanged: '=zemFacebookPageChanged',
        },
        controller: ['$scope', 'api', function ($scope, api) {
            $scope.facebookAccountStatusChecker = null;
            $scope.constants = constants;
            $scope.facebook = {page: $scope.facebookPage};

            $scope.$watch('facebookPage', function (newValue, oldValue) {
                if (newValue !== oldValue) {
                    $scope.checkFacebookAccountStatus();
                }
            });

            $scope.$watch('facebook.page', function (newValue, oldValue) {
                if (newValue !== oldValue) {
                    $scope.facebookPage = $scope.facebook.page;
                }
            });

            $scope.checkFacebookAccountStatus = function () {
                var facebookPage = $scope.facebookPage;
                var facebookStatus = $scope.facebookStatus;
                if (facebookPage === null || facebookStatus === constants.facebookStatus.CONNECTED) {
                    return;
                }
                api.accountSettings.getFacebookAccountStatus($scope.accountId).then(
                    function (data) {
                        var facebookAccountStatus = data.data.status;
                        $scope.facebookStatus = facebookAccountStatus;
                    },
                    function () {
                        $scope.facebookStatus = 'Error';
                    }
                );
                if ($scope.facebookAccountStatusChecker !== null) {
                    // prevent the creation of multiple Facebook account checkers (for example, when Facebook page URL is
                    // updated multiple times).
                    clearTimeout($scope.facebookAccountStatusChecker);
                }
                $scope.facebookAccountStatusChecker = setTimeout($scope.checkFacebookAccountStatus, 30 * 1000);
            };

            $scope.onFacebookPageChange = function () {
                $scope.facebookPageChanged = true;
            };

            $scope.clearFacebookPage = function () {
                $scope.facebookPage = null;
                $scope.facebook.page = null;
                $scope.facebookStatus = constants.facebookStatus.EMPTY;
                $scope.facebookPageChanged = true;
            };
        }]
    };
}]);
