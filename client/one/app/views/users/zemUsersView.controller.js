/* globals angular, constants */
angular.module('one.views').controller('zemUsersView', function ($scope, $timeout, zemNavigationNewService) { // eslint-disable-line max-len

    initialize();

    function initialize () {
        // WORKAROUND: Clear tab selection - not possible through uib API
        $('.uib-tab.active').removeClass('active');

        $scope.entity = zemNavigationNewService.getActiveEntity();
        if (!$scope.entity) {
            var handler = zemNavigationNewService.onActiveEntityChange(function () {
                $scope.entity = zemNavigationNewService.getActiveEntity();
                handler();
            });
        }
    }
});
