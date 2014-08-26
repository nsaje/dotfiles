/*global angular*/

var oneApp = angular.module('one', ['oneApi', 'ngBootstrap', 'ngSanitize', 'ui.router', 'ui.bootstrap', 'ui.bootstrap.datetimepicker', 'ui.select2', 'highcharts-ng', 'LocalStorageModule', 'config']);

oneApp.config(['$sceDelegateProvider', 'config', function ($sceDelegateProvider, config) {
    $sceDelegateProvider.resourceUrlWhitelist(['self', config.static_url + '/**']);
}]);

oneApp.config(['$httpProvider', function ($httpProvider) {
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
}]);

oneApp.config(["$locationProvider", function($locationProvider) {
    $locationProvider.html5Mode(true);
    $locationProvider.hashPrefix('!');

}]);

oneApp.config(['$stateProvider', '$urlRouterProvider', 'config', function ($stateProvider, $urlRouterProvider, config) {
    $urlRouterProvider.when('/signout', ['$location', function ($location) {
        window.location = $location.absUrl();
    }]);
    $urlRouterProvider.otherwise('/');

    var basicTemplate = '<ng-include src="config.static_url + \'/partials/tabset.html\'"></ng-include><div ui-view></div>'

    $stateProvider
        .state('main', {
            url: '/',
            templateUrl: config.static_url + '/partials/main.html',
            controller: 'MainCtrl',
            resolve: {
                user: ['api', function(api) {
                    return api.user.get('current');
                }],
                accounts: ['api', function (api) {
                    return api.navData.list();
                }],
            },
        });

    $stateProvider
        .state('main.allAccounts', {
            abstract: true,
            url: 'all_accounts',
            template: basicTemplate,
            controller: 'AllAccountsCtrl'
        })
        .state('main.allAccounts.accounts', {
            url: '/accounts',
            templateUrl: config.static_url + '/partials/all_accounts_accounts.html',
            controller: 'AllAccountsAccountsCtrl'

        });
    
    $stateProvider
        .state('main.accounts', {
            abstract: true,
            url: 'accounts/{id}',
            template: basicTemplate,
            controller: 'AccountCtrl'
        })
        .state('main.accounts.campaigns', {
            url: '/campaigns',
            templateUrl: config.static_url + '/partials/accounts_campaigns.html',
            controller: 'AccountCampaignsCtrl'
        });

    $stateProvider
        .state('main.campaigns', {
            abstract: true,
            url: 'campaigns/{id}',
            template: basicTemplate,
            controller: 'CampaignCtrl'
        })
        .state('main.campaigns.agency', {
            url: '/agency',
            templateUrl: config.static_url + '/partials/campaign_agency.html',
            controller: 'CampaignAgencyCtrl'
        });


    $stateProvider
        .state('main.adGroups', {
            abstract: true,
            url: 'ad_groups/{id}',
            templateUrl: config.static_url + '/partials/ad_group.html'
        })
        .state('main.adGroups.ads', {
            url: '/ads',
            templateUrl: config.static_url + '/partials/ad_group_contentads.html',
            controller: 'AdGroupAdsCtrl'
        })
        .state('main.adGroups.sources', {
            url: '/sources',
            templateUrl: config.static_url + '/partials/ad_group_sources.html',
            controller: 'AdGroupSourcesCtrl'
        })
        .state('main.adGroups.settings', {
            url: '/settings',
            templateUrl: config.static_url + '/partials/ad_group_settings.html',
            controller: 'AdGroupSettingsCtrl'
        })
        .state('main.adGroups.agency', {
            url: '/agency',
            templateUrl: config.static_url + '/partials/ad_group_agency.html',
            controller: 'AdGroupAgencyCtrl'
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
    $rootScope.$state = $state;

    $rootScope.$on('$stateChangeStart', function (e, toState, toParams, fromState, fromParams) {
        // Save location.search so we can add it back after transition is done
        locationSearch = $location.search();
    });

    $rootScope.$on('$stateChangeSuccess', function (e, toState, toParams, fromState, fromParams) {
        // Restore all query string parameters back to $location.search
        $location.search(locationSearch);
        $rootScope.stateChangeFired = true;
    });
}]);
