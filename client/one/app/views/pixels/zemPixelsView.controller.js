/* globals angular, constants */
angular.module('one.views').controller('zemPixelsView', function ($scope, $timeout, zemNavigationNewService) { // eslint-disable-line max-len

    initialize();

    function initialize () {
        // WORKAROUND: Clear tab selection - not possible through uib API
        $('.uib-tab.active').removeClass('active');

        $scope.account = zemNavigationNewService.getActiveAccount();
        if (!$scope.account) {
            var handler = zemNavigationNewService.onActiveEntityChange(function () {
                $scope.account = zemNavigationNewService.getActiveAccount();
                handler();
            });
        }
    }
});
