angular.module('one.views').config(function ($stateProvider) {
    // To conditionally navigate to a state include a data.canActivate property in state definition object. Example:
    // data: {
    //     canActivate: ['zemStateGuardService', 'myService', function (zemStateGuardService, myService) {
    //         // Return an array of promises that need to resolve in order to navigate to this state
    //         return [zemStateGuardService.checkPermission('[permission]'), myService.canActivate()];
    //     }],
    // }
    // NOTE: Explicitly annotated dependencies must be used - ngAnnotate grunt task can't automatically annotate them
    // NOTE: Nested states inherit state guard checks from parent states

    $stateProvider
        .state('v2', {
            url: '/v2',
            templateUrl: '/app/views/main/zemMainView.partial.html',
            abstract: true,
            controller: 'zemMainView as $ctrl',
            data: {
                canActivate: ['zemStateGuardService', function (zemStateGuardService) {
                    return [zemStateGuardService.canActivateMainState()];
                }],
            },
            resolve: {
                // Don't resolve until app is initialized
                initSequence: function (zemInitializationService) {
                    return zemInitializationService.initSequence();
                },
            },
        });

    $stateProvider
        .state('v2.analytics', {
            url: '/analytics/{level}/{id:int}/{breakdown}',
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
            },
        });

    $stateProvider
        .state('error', {
            url: '/error',
            template: '<ui-view/>',
            abstract: true,
        })
        .state('error.forbidden', {
            url: '/forbidden',
            templateUrl: '/partials/403.html',
        });
});
