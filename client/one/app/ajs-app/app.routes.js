angular.module('one').config(function($urlRouterProvider) {
    $urlRouterProvider.when('/signout', function($location) {
        window.location = $location.absUrl();
    });

    $urlRouterProvider.otherwise('/');

    $urlRouterProvider.rule(function($injector, $location) {
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
});
