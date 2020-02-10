var UiRouterStateName = require('../../app.constants').UiRouterStateName;

angular.module('one.views').config(function($stateProvider) {
    $stateProvider.state(UiRouterStateName.APP_BASE, {
        url: '/v2',
        template: require('./app/zemAppView.partial.html'),
        controller: 'zemAppView as $ctrl',
        resolve: {
            // Don't resolve until app is initialized
            initSequence: function(zemInitializationService) {
                return zemInitializationService.initSequence();
            },
        },
    });

    $stateProvider.state(UiRouterStateName.ANALYTICS, {
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

    $stateProvider.state(UiRouterStateName.CREATE_ENTITY, {
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

    $stateProvider.state(UiRouterStateName.REPORTS, {
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

    $stateProvider.state(UiRouterStateName.CREDIT, {
        url: '/credit/account/{id:int}',
        template: require('./account-credit/zemAccountCreditView.partial.html'),
        controller: 'zemAccountCreditView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state(UiRouterStateName.PUBLISHER_GROUPS, {
        url: '/publishergroups/account/{id:int}',
        template: require('./publisher-groups/zemPublisherGroupsView.partial.html'),
        controller: 'zemPublisherGroupsView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state(UiRouterStateName.USERS, {
        url: '/users/account/{id:int}',
        template: require('./users/zemUsersView.partial.html'),
        controller: 'zemUsersView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state(UiRouterStateName.PIXELS, {
        url: '/pixels/account/{id:int}',
        template: require('./pixels/zemPixelsView.partial.html'),
        controller: 'zemPixelsView as $ctrl',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state(UiRouterStateName.INVENTORY_PLANNING, {
        url: '/inventory-planning/',
        template: '<zem-inventory-planning-view></zem-inventory-planning-view>',
    });

    $stateProvider.state(UiRouterStateName.ARCHIVED, {
        url: '/archived/{level:account|campaign|adgroup}/{id:int}',
        template: require('./archived/zemArchivedView.partial.html'),
        controller: 'zemArchivedView as $ctrl',
    });

    $stateProvider.state(UiRouterStateName.DEALS_LIBRARY, {
        url: '/dealslibrary/{level:account}/{id:int}',
        template: '<zem-deals-library-view></zem-deals-library-view>',
        params: {
            id: {
                value: null,
                squash: true,
            },
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state(UiRouterStateName.ERROR_BASE, {
        url: '/error',
        template: '<ui-view/>',
        abstract: true,
    });

    $stateProvider.state(UiRouterStateName.ERROR_FORBIDDEN, {
        url: '/forbidden',
        template: require('./common/403.partial.html'),
        controller: function() {
            require('./common/403.partial.less');
        },
    });
});
