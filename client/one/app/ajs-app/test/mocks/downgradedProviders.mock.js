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
    });
