/*global angular*/

var oneApp = angular.module('one', ['ui.router', 'ui.bootstrap']);

oneApp.config(['$sceDelegateProvider', function ($sceDelegateProvider) {
    $sceDelegateProvider.resourceUrlWhitelist(['self', 'http://localhost:9999/**']);
}]);

oneApp.config(['$stateProvider', '$urlRouterProvider', function ($stateProvider, $urlRouterProvider) {
    $urlRouterProvider.otherwise('/');

    $stateProvider
        .state('adGroups', {
            abstract: true,
            url: '/ad_groups/{id}',
            template: '<ui-view/>'
        })
        .state('adGroups.ads', {
            url: '/ads',
            templateUrl: 'http://localhost:9999/partials/ad_group_ads.html',
            controller: 'AdGroupAdsCtrl'
        })
        .state('adGroups.networks', {
            url: '/networks',
            templateUrl: 'http://localhost:9999/partials/ad_group_networks.html',
            controller: 'AdGroupNetworksCtrl'
        })
        .state('adGroups.settings', {
            url: '/settings',
            templateUrl: 'http://localhost:9999/partials/ad_group_settings.html',
            controller: 'AdGroupSettingsCtrl'
        });
}]);

// Fixes https://github.com/angular-ui/ui-router/issues/679
oneApp.run(['$state', function($state){}]);
