/*global angular*/

var oneApp = angular.module('one', ['templates-one', 'ngBootstrap', 'ngSanitize', 'ui.router', 'ui.bootstrap', 'ui.bootstrap.tooltip', 'ui.bootstrap.datetimepicker', 'ui.select2', 'highcharts-ng', 'config', 'ui.select']);

oneApp.config(['$compileProvider', 'config', function ($compileProvider, config) {
    $compileProvider.debugInfoEnabled(config.debug);
}]);

oneApp.config(['$sceDelegateProvider', 'config', function ($sceDelegateProvider, config) {
    $sceDelegateProvider.resourceUrlWhitelist(['self', config.static_url + '/**']);
}]);

oneApp.config(['$httpProvider', function ($httpProvider) {
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
}]);

oneApp.config(['$locationProvider', function ($locationProvider) {
    $locationProvider.html5Mode(true);
    $locationProvider.hashPrefix('!');
}]);

oneApp.config(['$stateProvider', '$urlRouterProvider', 'config', function ($stateProvider, $urlRouterProvider, config) {
    $urlRouterProvider.when('/signout', ['$location', function ($location) {
        window.location = $location.absUrl();
    }]);
    $urlRouterProvider.when('/demo_mode', ['$location', function ($location) {
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

    var basicTemplate = '<ng-include src="\'/partials/tabset.html\'"></ng-include><div ui-view></div>';

    $stateProvider
        .state('main', {
            url: '/',
            templateUrl: '/partials/main.html',
            controller: 'MainCtrl',
            resolve: {
                user: ['api', 'zemLocalStorageService', 'zemFilterService', function (api, zemLocalStorageService, zemFilterService) {
                    return api.user.get('current').then(function (user) {
                        zemLocalStorageService.init(user);
                        zemFilterService.init(user);
                        return user;
                    });
                }],
                accountsAccess: ['zemNavigationService', function (zemNavigationService) {
                    return zemNavigationService.getAccountsAccess();
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
        })
        .state('main.allAccounts.scheduled_reports', {
            url: '/reports',
            templateUrl: '/partials/scheduled_reports.html',
            controller: 'ScheduledReportsCtrl'
        });

    $stateProvider
        .state('main.accounts', {
            url: 'accounts/{id}',
            template: basicTemplate,
            controller: 'AccountCtrl',
            resolve: {
                accountData: ['$stateParams', 'zemNavigationService', function ($stateParams, zemNavigationService) {
                    return zemNavigationService.getAccount($stateParams.id);
                }],
            },
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
        })
        .state('main.accounts.settings', {
            url: '/settings',
            templateUrl: '/partials/account_account.html',
            controller: 'AccountAccountCtrl'
        })
        .state('main.accounts.archived', {
            url: '/archived',
            templateUrl: '/partials/account_settings.html'
        }).state('main.accounts.credit', {
            url: '/credit',
            templateUrl: '/partials/account_credit.html',
            controller: 'AccountCreditCtrl'
        }).state('main.accounts.scheduled_reports', {
            url: '/reports',
            templateUrl: '/partials/scheduled_reports.html',
            controller: 'ScheduledReportsCtrl'
        });

    $stateProvider
        .state('main.campaigns', {
            url: 'campaigns/{id}',
            template: basicTemplate,
            controller: 'CampaignCtrl',
            resolve: {
                campaignData: ['$stateParams', 'zemNavigationService', function ($stateParams, zemNavigationService) {
                    return zemNavigationService.getCampaign($stateParams.id);
                }],
            },
        })
        .state('main.campaigns.ad_groups', {
            url: '/ad_groups',
            templateUrl: '/partials/campaign_ad_groups.html',
            controller: 'CampaignAdGroupsCtrl',
        })
        .state('main.campaigns.sources', {
            url: '/sources',
            templateUrl: '/partials/media_sources.html',
            controller: 'MediaSourcesCtrl',
        })
        .state('main.campaigns.agency', {
            url: '/agency',
            templateUrl: '/partials/campaign_agency.html',
            controller: 'CampaignAgencyCtrl',
        })
        .state('main.campaigns.archived', {
            url: '/archived',
            templateUrl: '/partials/campaign_archived.html',
        })
        .state('main.campaigns.settings', {
            url: '/settings',
            templateUrl: '/partials/campaign_settings.html',
            controller: 'CampaignSettingsCtrl',
        })
        .state('main.campaigns.budget', {
            url: '/budget',
            templateUrl: '/partials/campaign_budget.html',
            controller: 'CampaignBudgetCtrl',
        });


    $stateProvider
        .state('main.adGroups', {
            url: 'ad_groups/{id}',
            template: basicTemplate,
            controller: 'AdGroupCtrl',
            resolve: {
                adGroupData: ['$stateParams', 'zemNavigationService', function ($stateParams, zemNavigationService) {
                    return zemNavigationService.getAdGroup($stateParams.id);
                }],
            },
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
        })
        .state('main.adGroups.adsPlus', {
            url: '/ads_plus',
            templateUrl: '/partials/ad_group_contentadsplus.html',
            controller: 'AdGroupAdsPlusCtrl'
        })
        .state('main.adGroups.publishers', {
            url: '/publishers',
            templateUrl: '/partials/ad_group_publishers.html',
            controller: 'AdGroupPublishersCtrl'
        })

        ;
}]);

oneApp.config(['datepickerConfig', 'datepickerPopupConfig', function (datepickerConfig, datepickerPopupConfig) {
    datepickerConfig.showWeeks = false;
    datepickerConfig.formatDayHeader = 'EEE';
    datepickerPopupConfig.showButtonBar = false;
}]);

oneApp.config(['$tooltipProvider', function ($tooltipProvider) {
    $tooltipProvider.setTriggers({'openTutorial': 'closeTutorial'});
}]);

var locationSearch;
// Fixes https://github.com/angular-ui/ui-router/issues/679
oneApp.run(['$state', '$rootScope', '$location', 'config', 'zemIntercomService', function ($state, $rootScope, $location, config, zemIntercomService) {
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

    $rootScope.$on('$locationChangeSuccess', function () {
        zemIntercomService.update();
    });

    $rootScope.tabClick = function (event) {
        // Function to fix opening tabs in new tab when clicking with the middle button
        // This is effectively a workaround for a bug in bootstrap-ui
        if (event.which === 2 || (event.which === 1 && (event.metaKey || event.ctrlKey))) {
           // MIDDLE CLICK or CMD+LEFTCLICK
           // the regular link will open in new tab if we stop the event propagation
            event.stopPropagation();
        }
    };

}]);
