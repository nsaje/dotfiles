/*global angular*/

var oneApp = angular.module('one', ['templates-dist', 'oneApi', 'ngBootstrap', 'ngSanitize', 'ui.router', 'ui.bootstrap', 'ui.bootstrap.datetimepicker', 'ui.select2', 'highcharts-ng', 'LocalStorageModule', 'config']);

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

    var basicTemplate = '<ng-include src="\'/partials/tabset.html\'"></ng-include><div ui-view></div>'

    $stateProvider
        .state('main', {
            url: '/',
            templateUrl: '/partials/main.html',
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
            url: 'all_accounts',
            template: basicTemplate,
            controller: 'AllAccountsCtrl'
        })
        .state('main.allAccounts.accounts', {
            url: '/accounts',
            templateUrl: '/partials/all_accounts_accounts.html',
            controller: 'AllAccountsAccountsCtrl'
        })
        .state('main.allAccounts.sources', {
            url: '/sources',
            templateUrl: '/partials/media_sources.html',
            controller: 'MediaSourcesCtrl'
        });

    $stateProvider
        .state('main.accounts', {
            url: 'accounts/{id}',
            template: basicTemplate,
            controller: 'AccountCtrl'
        })
        .state('main.accounts.campaigns', {
            url: '/campaigns',
            templateUrl: '/partials/account_campaigns.html',
            controller: 'AccountCampaignsCtrl'
        })
        .state('main.accounts.sources', {
            url: '/sources',
            templateUrl: '/partials/media_sources.html',
            controller: 'MediaSourcesCtrl'
        })
        .state('main.accounts.agency', {
            url: '/agency',
            templateUrl: '/partials/account_agency.html',
            controller: 'AccountAgencyCtrl'
        });

    $stateProvider
        .state('main.campaigns', {
            url: 'campaigns/{id}',
            template: basicTemplate,
            controller: 'CampaignCtrl'
        })
        .state('main.campaigns.ad_groups', {
            url: '/ad_groups',
            templateUrl: '/partials/campaign_ad_groups.html',
            controller: 'CampaignAdGroupsCtrl'
        })
        .state('main.campaigns.sources', {
            url: '/sources',
            templateUrl: '/partials/media_sources.html',
            controller: 'MediaSourcesCtrl'
        })
        .state('main.campaigns.agency', {
            url: '/agency',
            templateUrl: '/partials/campaign_agency.html',
            controller: 'CampaignAgencyCtrl'
        });


    $stateProvider
        .state('main.adGroups', {
            url: 'ad_groups/{id}',
            templateUrl: '/partials/ad_group.html'
        })
        .state('main.adGroups.ads', {
            url: '/ads',
            templateUrl: '/partials/ad_group_contentads.html',
            controller: 'AdGroupAdsCtrl'
        })
        .state('main.adGroups.sources', {
            url: '/sources',
            templateUrl: '/partials/ad_group_sources.html',
            controller: 'AdGroupSourcesCtrl'
        })
        .state('main.adGroups.settings', {
            url: '/settings',
            templateUrl: '/partials/ad_group_settings.html',
            controller: 'AdGroupSettingsCtrl'
        })
        .state('main.adGroups.agency', {
            url: '/agency',
            templateUrl: '/partials/ad_group_agency.html',
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
