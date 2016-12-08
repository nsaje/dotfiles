/* global angular */

angular.module('one.legacy', []);

angular.module('one.legacy').config(function ($stateProvider) {
    var basicTemplate = '<ng-include src="\'/partials/tabset.html\'"></ng-include><div ui-view></div>';

    $stateProvider
        .state('main', {
            url: '/',
            templateUrl: '/partials/main.html',
            controller: 'MainCtrl',
            resolve: {
                initServices: function (zemUserService, zemSettingsService, zemFilterService, zemDataFilterService, zemNavigationNewService, zemMediaSourcesService) {
                    // Service initialization - TODO: find cleaner solution
                    zemNavigationNewService.init();
                    zemMediaSourcesService.init();
                    zemSettingsService.init();
                    return zemUserService.init().then(function () {
                        zemDataFilterService.init();
                        zemFilterService.init();
                    });
                },
                accountsAccess: function (zemNavigationService) {
                    return zemNavigationService.getAccountsAccess();
                },
            },
        });

    $stateProvider
        .state('main.allAccounts', {
            url: 'all_accounts',
            template: basicTemplate,
            controller: 'AllAccountsCtrl',
        })
        .state('main.allAccounts.accounts', {
            url: '/accounts',
            templateUrl: '/partials/all_accounts_accounts.html',
            controller: 'AllAccountsAccountsCtrl',
        })
        .state('main.allAccounts.sources', {
            url: '/sources',
            templateUrl: '/partials/media_sources.html',
            controller: 'MediaSourcesCtrl',
        })
        .state('main.allAccounts.scheduled_reports', {
            url: '/reports',
            templateUrl: '/partials/scheduled_reports.html',
            controller: 'ScheduledReportsCtrl',
        });

    $stateProvider
        .state('main.accounts', {
            url: 'accounts/{id}',
            template: basicTemplate,
            controller: 'AccountCtrl',
            resolve: {
                accountData: function ($stateParams, zemNavigationService) {
                    return zemNavigationService.getAccount($stateParams.id);
                },
            },
        })
        .state('main.accounts.campaigns', {
            url: '/campaigns?settings',
            templateUrl: '/partials/account_campaigns.html',
            controller: 'AccountCampaignsCtrl',
        })
        .state('main.accounts.sources', {
            url: '/sources',
            templateUrl: '/partials/media_sources.html',
            controller: 'MediaSourcesCtrl',
        })
        .state('main.accounts.history', {
            url: '/history',
            templateUrl: '/partials/account_history.html',
            controller: 'AccountHistoryCtrl',
        })
        .state('main.accounts.settings', {
            url: '/settings',
            templateUrl: '/partials/account_account.html',
            controller: 'AccountAccountCtrl',
        })
        .state('main.accounts.archived', {
            // Temporary solution for archived
            url: '/archived',
            templateUrl: '/partials/archived_entity.html',
            controller: 'ArchivedEntityCtrl'
        })
        .state('main.accounts.customAudiences', {
            url: '/audiences',
            templateUrl: '/partials/account_custom_audiences.html',
            controller: 'AccountCustomAudiencesCtrl',
        }).state('main.accounts.credit', {
            url: '/credit',
            templateUrl: '/partials/account_credit.html',
            controller: 'AccountCreditCtrl',
        }).state('main.accounts.scheduled_reports', {
            url: '/reports',
            templateUrl: '/partials/scheduled_reports.html',
            controller: 'ScheduledReportsCtrl',
        });

    $stateProvider
        .state('main.campaigns', {
            url: 'campaigns/{id}',
            template: basicTemplate,
            controller: 'CampaignCtrl',
            resolve: {
                campaignData: function ($stateParams, zemNavigationService) {
                    return zemNavigationService.getCampaign($stateParams.id);
                },
            },
        })
        .state('main.campaigns.ad_groups', {
            url: '/ad_groups?settings',
            templateUrl: '/partials/campaign_ad_groups.html',
            controller: 'CampaignAdGroupsCtrl',
        })
        .state('main.campaigns.sources', {
            url: '/sources',
            templateUrl: '/partials/media_sources.html',
            controller: 'MediaSourcesCtrl',
        })
        .state('main.campaigns.settings', {
            url: '/settings',
            templateUrl: '/partials/campaign_settings.html',
            controller: 'CampaignSettingsCtrl',
        })
        .state('main.campaigns.archived', {
            // Temporary solution for archived
            url: '/archived',
            templateUrl: '/partials/archived_entity.html',
            controller: 'ArchivedEntityCtrl'
        })
        .state('main.campaigns.history', {
            url: '/history',
            templateUrl: '/partials/campaign_history.html',
            controller: 'CampaignHistoryCtrl',
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
                adGroupData: function ($stateParams, zemNavigationService) {
                    return zemNavigationService.getAdGroup($stateParams.id);
                },
            },
        })
        .state('main.adGroups.adsplus', {
            url: '/ads_plus',
            abstract: true,
        })
        .state('main.adGroups.ads', {
            url: '/ads?settings',
            templateUrl: '/partials/ad_group_contentads.html',
            controller: 'AdGroupAdsCtrl',
        })
        .state('main.adGroups.sources', {
            url: '/sources',
            templateUrl: '/partials/ad_group_sources.html',
            controller: 'AdGroupSourcesCtrl',
        })
        .state('main.adGroups.settings', {
            url: '/settings',
            templateUrl: '/partials/ad_group_settings.html',
            controller: 'AdGroupSettingsCtrl',
        })
        .state('main.adGroups.history', {
            url: '/history',
            templateUrl: '/partials/ad_group_history.html',
            controller: 'AdGroupHistoryCtrl',
        })
        .state('main.adGroups.publishers', {
            url: '/publishers',
            templateUrl: '/partials/ad_group_publishers.html',
            controller: 'AdGroupPublishersCtrl',
        })
        .state('main.adGroups.archived', {
            // Temporary solution for archived
            url: '/archived',
            templateUrl: '/partials/archived_entity.html',
            controller: 'ArchivedEntityCtrl'
        });
});
