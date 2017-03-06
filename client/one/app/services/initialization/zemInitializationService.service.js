angular.module('one.services').service('zemInitializationService', function ($q, zemUserService, zemStateGuardService, zemMediaSourcesService, zemNavigationNewService, zemNavigationService, zemDataFilterService, zemFullStoryService, zemIntercomService, zemSupportHeroService) { // eslint-disable-line max-len
    this.initApp = initApp;
    this.initSequence = initSequence;

    var sequence;

    function initApp () {
        // NOTE: zemStateGuardService should init first to set a guard check to $stateChangeStart event before any such
        // event is emitted from ui-router
        zemStateGuardService.init();

        zemNavigationNewService.init();
        zemMediaSourcesService.init();
        zemNavigationService.reload();

        // Service initializers that need to resolve before user can use the app
        sequence = $q.all([
            initZemUserServiceAndDependantServices()
        ]);

        return sequence;
    }

    function initSequence () {
        return initSequence;
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
