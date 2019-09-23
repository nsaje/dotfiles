angular.module('one.views').config(function($stateProvider) {
    $stateProvider.state('v2', {
        url: '/v2',
        template: require('./main/zemMainView.partial.html'),
        controller: 'zemMainView as $ctrl',
        resolve: {
            // Don't resolve until app is initialized
            initSequence: function(zemInitializationService) {
                return zemInitializationService.initSequence();
            },
        },
    });

    $stateProvider.state('v2.analytics', {
        url:
            '/analytics/{level:accounts|account|campaign|adgroup}/{id:int}/{breakdown}',
        template: require('./analytics/zemAnalyticsView.partial.html'),
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

    $stateProvider.state('v2.createEntity', {
        url: '/create/{level:account|campaign|adgroup}/{id:int}',
        template:
            '<zem-new-entity-analytics-mock-view></zem-new-entity-analytics-mock-view>',
        params: {
            id: {
                value: null,
                squash: true,
            },
        },
    });

    $stateProvider.state('v2.reports', {
        url: '/reports/{level:accounts|account}/{id:int}',
        template: require('./scheduled-reports/zemScheduledReports.partial.html'),
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
        template: require('./account-credit/zemAccountCreditView.partial.html'),
        controller: 'zemAccountCreditView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state('v2.publisherGroups', {
        url: '/publishergroups/account/{id:int}',
        template: require('./publisher-groups/zemPublisherGroupsView.partial.html'),
        controller: 'zemPublisherGroupsView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state('v2.users', {
        url: '/users/account/{id:int}',
        template: require('./users/zemUsersView.partial.html'),
        controller: 'zemUsersView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state('v2.pixels', {
        url: '/pixels/account/{id:int}',
        template: require('./pixels/zemPixelsView.partial.html'),
        controller: 'zemPixelsView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state('v2.inventoryPlanning', {
        url: '/inventory-planning/',
        template: '<zem-inventory-planning-view></zem-inventory-planning-view>',
    });

    $stateProvider.state('v2.archived', {
        url: '/archived/{level:account|campaign|adgroup}/{id:int}',
        template: require('./archived/zemArchivedView.partial.html'),
        controller: 'zemArchivedView as $ctrl',
    });

    $stateProvider.state('v2.dealsLibrary', {
        url: '/dealslibrary/account/{id:int}',
        template: require('./deals/zemDealsLibraryView.partial.html'),
        controller: 'zemDealsLibraryView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state('error', {
        url: '/error',
        template: '<ui-view/>',
        abstract: true,
    });

    $stateProvider.state('error.forbidden', {
        url: '/forbidden',
        template: require('./common/403.partial.html'),
        controller: function() {
            require('./common/403.partial.less');
        },
    });
});
