var mockedFunction = function() {};

angular
    .module('one.mocks.downgradedProviders', [])
    .service('zemMulticurrencyService', function() {
        this.getValueInAppropriateCurrency = mockedFunction;
        this.getAppropriateCurrencySymbol = mockedFunction;
    })
    .service('zemCampaignGoalsService', function() {
        this.getAvailableGoals = mockedFunction;
    });
