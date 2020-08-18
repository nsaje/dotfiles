angular
    .module('one.services')
    .service('zemInitializationService', function(
        zemAuthStore,
        zemMediaSourcesService,
        zemNavigationNewService,
        zemNavigationService,
        zemDataFilterService,
        zemIntercomService,
        zemSupportHeroService
    ) {
        this.initApp = initApp;

        function initApp() {
            // TODO (msuber): refactor to ng
            zemNavigationNewService.init();
            zemMediaSourcesService.init();
            zemNavigationService.init();
            zemDataFilterService.init();
            zemIntercomService.boot(zemAuthStore.getCurrentUser());
            zemSupportHeroService.boot(zemAuthStore.getCurrentUser());
        }
    });
