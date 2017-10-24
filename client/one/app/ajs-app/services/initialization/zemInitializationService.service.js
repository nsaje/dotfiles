angular.module('one.services').service('zemInitializationService', function ($q, zemUserService, zemMediaSourcesService, zemNavigationNewService, zemNavigationService, zemDataFilterService, zemFullStoryService, zemIntercomService, zemSupportHeroService, zemDesignHelpersService, zemGoogleAnalyticsService) { // eslint-disable-line max-len
    this.initApp = initApp;
    this.initSequence = initSequence;

    var sequence;

    function initApp () {
        zemNavigationNewService.init();
        zemMediaSourcesService.init();
        zemNavigationService.init();

        zemGoogleAnalyticsService.init();
        zemDesignHelpersService.init();

        // Service initializers that need to resolve before user can use the app
        sequence = $q.all([
            initZemUserServiceAndDependantServices()
        ]);

        return sequence;
    }

    function initSequence () {
        return sequence;
    }

    function initZemUserServiceAndDependantServices () {
        return zemUserService.init().then(function () {
            zemDataFilterService.init();

            zemFullStoryService.identifyUser(zemUserService.current());
            zemIntercomService.boot(zemUserService.current());
            zemSupportHeroService.boot(zemUserService.current());
        });
    }
});
