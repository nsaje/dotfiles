/* global angular */

angular.module('one.legacy', []);

angular.module('one.legacy').config(function ($stateProvider) {

    // If new routing is used skip legacy state initialization
    if (window.APP && window.APP.USE_NEW_ROUTING) return;

    var basicTemplate = '<ng-include src="\'/partials/tabset.html\'"></ng-include><div ui-view></div>';

    $stateProvider
        .state('main', {
            url: '/',
            templateUrl: '/partials/main.html',
            controller: 'MainCtrl',
            resolve: {
                // Don't resolve until app is initialized
                initSequence: function (zemInitializationService) {
                    return zemInitializationService.initSequence();
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
        })
        .state('main.allAccounts.scheduled_reports_v2', {
            url: '/reports_v2',
            templateUrl: '/app/views/scheduled-reports/zemScheduledReports.partial.html',
            controller: 'zemScheduledReportsView as $ctrl',
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
            url: '/campaigns',
            params: {settings: null, settingsScrollTo: null},
            templateUrl: '/partials/account_campaigns.html',
            controller: 'AccountCampaignsCtrl',
        })
        .state('main.accounts.sources', {
            url: '/sources',
            templateUrl: '/partials/media_sources.html',
            controller: 'MediaSourcesCtrl',
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
        }).state('main.accounts.credit_v2', {
            url: '/credit_v2',
            templateUrl: '/app/views/account-credit/zemAccountCreditView.partial.html',
            controller: 'zemAccountCreditView as $ctrl',
        }).state('main.accounts.scheduled_reports', {
            url: '/reports',
            templateUrl: '/partials/scheduled_reports.html',
            controller: 'ScheduledReportsCtrl',
        }).state('main.accounts.publisherGroups', {
            url: '/publishergroups',
            templateUrl: '/app/views/publisher-groups/zemPublisherGroupsView.partial.html',
            controller: 'zemPublisherGroupsView as $ctrl',
        })
        .state('main.accounts.scheduled_reports_v2', {
            url: '/reports_v2',
            templateUrl: '/app/views/scheduled-reports/zemScheduledReports.partial.html',
            controller: 'zemScheduledReportsView as $ctrl',
        }).state('main.accounts.users', {
            url: '/users',
            templateUrl: '/app/views/users/zemUsersView.partial.html',
            controller: 'zemUsersView as $ctrl',
        }).state('main.accounts.pixels', {
            url: '/pixels',
            templateUrl: '/app/views/pixels/zemPixelsView.partial.html',
            controller: 'zemPixelsView as $ctrl',
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
            url: '/ad_groups',
            params: {settings: null, settingsScrollTo: null},
            templateUrl: '/partials/campaign_ad_groups.html',
            controller: 'CampaignAdGroupsCtrl',
        })
        .state('main.campaigns.sources', {
            url: '/sources',
            templateUrl: '/partials/media_sources.html',
            controller: 'MediaSourcesCtrl',
        })
        .state('main.campaigns.archived', {
            // Temporary solution for archived
            url: '/archived',
            templateUrl: '/partials/archived_entity.html',
            controller: 'ArchivedEntityCtrl'
        })
        .state('main.campaigns.insights', {
            url: '/insights',
            templateUrl: '/partials/campaign_insights.html',
            controller: 'CampaignInsightsCtrl',
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
            url: '/ads',
            params: {settings: null, settingsScrollTo: null},
            templateUrl: '/partials/ad_group_contentads.html',
            controller: 'AdGroupAdsCtrl',
        })
        .state('main.adGroups.sources', {
            url: '/sources',
            templateUrl: '/partials/ad_group_sources.html',
            controller: 'AdGroupSourcesCtrl',
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
