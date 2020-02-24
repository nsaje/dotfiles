var empty = require('rxjs').empty;

angular
    .module('one.mocks.downgradedProviders', [])
    .service('zemEntitiesUpdatesService', function() {
        this.getAllUpdates$ = function() {
            return empty();
        };
        this.getUpdatesOfEntity$ = function() {
            return empty();
        };
    })
    .service('zemBidModifierUpdatesService', function() {
        this.getAllUpdates$ = function() {
            return empty();
        };
    })
    .service('zemAccountService', function() {
        this.list = function() {
            return empty();
        };
    })
    .service('zemExceptionHandlerService', function() {
        this.handleHttpException = function() {
            return empty();
        };
        this.shouldRetryRequest = function() {
            return empty();
        };
        this.getRequestRetryTimeout = function() {
            return empty();
        };
    });
