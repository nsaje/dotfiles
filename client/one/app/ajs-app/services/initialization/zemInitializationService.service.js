angular
    .module('one.services')
    .service('zemInitializationService', function(
        $q,
        zemUserService,
        zemMediaSourcesService,
        zemNavigationNewService,
        zemNavigationService,
        zemDataFilterService,
        zemIntercomService,
        zemSupportHeroService,
        zemGoogleAnalyticsService,
        zemMixpanelService
    ) {
        // eslint-disable-line max-len
        this.initApp = initApp;
        this.initSequence = initSequence;

        var sequence;

        function initApp() {
            zemNavigationNewService.init();
            zemMediaSourcesService.init();
            zemNavigationService.init();

            zemGoogleAnalyticsService.init();
            zemMixpanelService.init();

            // Service initializers that need to resolve before user can use the app
            sequence = $q.all([initZemUserServiceAndDependantServices()]);

            return sequence;
        }

        function initSequence() {
            return sequence;
        }

        function initZemUserServiceAndDependantServices() {
            return zemUserService.init().then(function() {
                zemDataFilterService.init();

                zemIntercomService.boot(zemUserService.current());
                zemSupportHeroService.boot(zemUserService.current());
            });
        }
    });
