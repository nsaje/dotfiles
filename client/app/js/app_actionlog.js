/*global angular*/

var oneActionLogApp = angular.module('one-actionlog', ['oneApi', 'ui.router', 'ui.bootstrap', 'config', 'templates-dist']);

oneActionLogApp.config(['$sceDelegateProvider', 'config', function ($sceDelegateProvider, config) {
    $sceDelegateProvider.resourceUrlWhitelist(['self', config.static_url + '/**']);
}]);

oneActionLogApp.config(['$httpProvider', function ($httpProvider) {
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
}]);

var locationSearch;
oneActionLogApp.run(['$state', '$rootScope', '$location', 'config', function($state, $rootScope, $location, config) {
    $rootScope.config = config;
    $rootScope.$state = $state;

    $rootScope.$on('$stateChangeStart', function (e, toState, toParams, fromState, fromParams) {
        // Save location.search so we can add it back after transition is done
        locationSearch = $location.search();
    });

    $rootScope.$on('$stateChangeSuccess', function (e, toState, toParams, fromState, fromParams) {
        // Restore all query string parameters back to $location.search
        $location.search(locationSearch);
    });
}]);

