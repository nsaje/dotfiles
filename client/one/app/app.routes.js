/* global angular */

angular.module('one').config(['$urlRouterProvider', function ($urlRouterProvider) {
    $urlRouterProvider.when('/signout', ['$location', function ($location) {
        window.location = $location.absUrl();
    }]);

    $urlRouterProvider.when('/ad_groups/:adGroupId/ads_plus', '/ad_groups/:adGroupId/ads');

    $urlRouterProvider.otherwise('/');

    $urlRouterProvider.rule(function ($injector, $location) {
        var path = $location.url();

        // check to see if the path has a trailing slash
        if ('/' === path[path.length - 1]) {
            return path.replace(/\/$/, '');
        }

        if (path.indexOf('/?') > -1) {
            return path.replace('/?', '?');
        }

        return false;
    });
}]);
