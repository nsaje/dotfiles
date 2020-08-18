angular
    .module('one.mocks.zemInitializationService', [])
    .service('zemInitializationService', function($q) {
        this.initApp = initApp;

        function initApp() {
            return $q.resolve();
        }
    });
