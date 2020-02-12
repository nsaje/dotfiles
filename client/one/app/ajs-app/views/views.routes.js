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
        template: '<zem-analytics-view></zem-analytics-view>',
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
        template: '<zem-reports-library-view></zem-reports-library-view>',
        params: {
            id: {
                value: null,
                squash: true,
            },
        },
    });

    $stateProvider.state(UiRouterStateName.CREDIT, {
        url: '/credit/{level:account}/{id:int}',
        template: '<zem-credits-library-view></zem-credits-library-view>',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state(UiRouterStateName.PUBLISHER_GROUPS, {
        url: '/publishergroups/{level:account}/{id:int}',
        template:
            '<zem-publisher-groups-library-view></zem-publisher-groups-library-view>',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state(UiRouterStateName.USERS, {
        url: '/users/{level:account}/{id:int}',
        template: '<zem-users-library-view></zem-users-library-view>',
        params: {
            level: constants.levelStateParam.ACCOUNT,
        },
    });

    $stateProvider.state(UiRouterStateName.PIXELS, {
        url: '/pixels/{level:account}/{id:int}',
        template: '<zem-pixels-library-view></zem-pixels-library-view>',
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
        template: '<zem-archived-view></zem-archived-view>',
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
        template: '<zem-error-forbidden-view></zem-error-forbidden-view>',
    });
});
