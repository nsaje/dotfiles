angular.module('one.views').config(function ($stateProvider) {
    $stateProvider.state('v2', {
        url: '/v2',
        templateUrl: '/app/views/main/zemMainView.partial.html',
        controller: 'zemMainView as $ctrl',
        resolve: {
            // Don't resolve until app is initialized
            initSequence: function (zemInitializationService) {
                return zemInitializationService.initSequence();
            },
        },
    });

    $stateProvider.state('v2.analytics', {
        url: '/analytics/{level:accounts|account|campaign|adgroup}/{id:int}/{breakdown}',
        templateUrl: '/app/views/analytics/zemAnalyticsView.partial.html',
        controller: 'zemAnalyticsView as $ctrl',
        params: {
            id: {
                value: null,
                squash: true,
            },
            breakdown: {
                value: null,
                squash: true,
            },
            settings: null,
            settingsScrollTo: null,
            history: null,
        },
    });

    $stateProvider.state('v2.reports', {
        url: '/reports/{level:accounts|account}/{id:int}',
        templateUrl: '/app/views/scheduled-reports/zemScheduledReports.partial.html',
        controller: 'zemScheduledReportsView as $ctrl',
        params: {
            id: {
                value: null,
                squash: true,
            },
        },
    });

    $stateProvider.state('v2.accountCredit', {
        url: '/credit/account/{id:int}',
        templateUrl: '/app/views/account-credit/zemAccountCreditView.partial.html',
        controller: 'zemAccountCreditView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state('v2.publisherGroups', {
        url: '/publishergroups/account/{id:int}',
        templateUrl: '/app/views/publisher-groups/zemPublisherGroupsView.partial.html',
        controller: 'zemPublisherGroupsView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state('v2.users', {
        url: '/users/account/{id:int}',
        templateUrl: '/app/views/users/zemUsersView.partial.html',
        controller: 'zemUsersView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state('v2.pixels', {
        url: '/pixels/account/{id:int}',
        templateUrl: '/app/views/pixels/zemPixelsView.partial.html',
        controller: 'zemPixelsView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state('v2.archived', {
        url: '/archived/{level:account|campaign|adgroup}/{id:int}',
        templateUrl: '/app/views/archived/zemArchivedView.partial.html',
        controller: 'zemArchivedView as $ctrl',
    });

    $stateProvider.state('error', {
        url: '/error',
        template: '<ui-view/>',
        abstract: true,
    });

    $stateProvider.state('error.forbidden', {
        url: '/forbidden',
        templateUrl: '/app/views/common/403.partial.html',
    });
});
