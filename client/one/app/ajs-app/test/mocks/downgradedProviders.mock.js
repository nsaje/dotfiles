var empty = require('rxjs').empty;

var mockedFunction = function() {};

angular
    .module('one.mocks.downgradedProviders', [])
    .service('zemMulticurrencyService', function() {
        this.getValueInAppropriateCurrency = mockedFunction;
        this.getAppropriateCurrencySymbol = mockedFunction;
    })
    .service('zemCampaignGoalsService', function() {
        this.getAvailableGoals = mockedFunction;
    })
    .service('zemEntitiesUpdatesService', function() {
        this.getAllUpdates$ = empty();
        this.getUpdatesOfEntity$ = empty();
    });
