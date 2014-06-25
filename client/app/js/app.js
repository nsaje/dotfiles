/*global angular*/

var oneApp = angular.module('one', ['ngSanitize', 'ui.router', 'ui.bootstrap', 'ui.bootstrap.datetimepicker', 'ui.select2', 'highcharts-ng', 'config']);

oneApp.config(['$sceDelegateProvider', 'config', function ($sceDelegateProvider, config) {
    $sceDelegateProvider.resourceUrlWhitelist(['self', config.static_url + '/**']);
}]);

oneApp.config(['$httpProvider', function ($httpProvider) {
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
}]);

oneApp.config(['$stateProvider', '$urlRouterProvider', 'config', function ($stateProvider, $urlRouterProvider, config) {
    $urlRouterProvider.otherwise('/');

    $stateProvider
        .state('adGroups', {
            abstract: true,
            url: '/ad_groups/{id}',
            template: '<ui-view/>'
        })
        .state('adGroups.ads', {
            url: '/ads',
            templateUrl: config.static_url + '/partials/ad_group_ads.html',
            controller: 'AdGroupAdsCtrl',
            reloadOnSearch: false
        })
        .state('adGroups.networks', {
            url: '/networks',
            templateUrl: config.static_url + '/partials/ad_group_networks.html',
            controller: 'AdGroupNetworksCtrl',
            reloadOnSearch: false
        })
        .state('adGroups.settings', {
            url: '/settings',
            templateUrl: config.static_url + '/partials/ad_group_settings.html',
            controller: 'AdGroupSettingsCtrl',
            reloadOnSearch: false
        });
}]);

oneApp.config(['datepickerConfig', 'datepickerPopupConfig', function (datepickerConfig, datepickerPopupConfig) {
  datepickerConfig.showWeeks = false;
  datepickerConfig.formatDayHeader = 'EEE';
  datepickerPopupConfig.showButtonBar = false;
}]);

var locationSearch;
// Fixes https://github.com/angular-ui/ui-router/issues/679
oneApp.run(['$state', '$rootScope', '$location', 'config', function($state, $rootScope, $location, config) {
    $rootScope.config = config;

    $rootScope.$on('$stateChangeStart', function (e, toState, toParams, fromState, fromParams) {
        // Save location.search so we can add it back after transition is done
        locationSearch = $location.search();
    });

    $rootScope.$on('$stateChangeSuccess', function (e, toState, toParams, fromState, fromParams) {
        // Restore all query string parameters back to $location.search
        $location.search(locationSearch);
    });
}]);
