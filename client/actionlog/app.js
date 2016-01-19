/*global angular*/

var actionLogApp = angular.module('actionlog', ['ui.bootstrap', 'config']);

actionLogApp.config(['$sceDelegateProvider', 'config', function ($sceDelegateProvider, config) {
    $sceDelegateProvider.resourceUrlWhitelist(['self', config.static_url + '/actionlog/**']);
}]);

actionLogApp.config(['$httpProvider', function ($httpProvider) {
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
}]);

var locationSearch;
actionLogApp.run(['$rootScope', 'config', function($rootScope, config) {
    $rootScope.config = config;
}]);

