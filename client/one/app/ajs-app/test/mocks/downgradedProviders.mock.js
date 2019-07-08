var empty = require('rxjs').empty;

angular
    .module('one.mocks.downgradedProviders', [])
    .service('zemEntitiesUpdatesService', function() {
        this.getAllUpdates$ = empty();
        this.getUpdatesOfEntity$ = empty();
    });
