angular
    .module('one.mocks.zemInitializationService', [])
    .service('zemInitializationService', function($q) {
        this.initApp = initApp;
        this.initSequence = initSequence;

        function initApp() {
            return $q.resolve();
        }

        function initSequence() {
            return $q.resolve();
        }
    });
