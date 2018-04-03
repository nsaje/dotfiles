angular.module('one.widgets').component('zemCampaignBudgetOptimizationSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemCampaignBudgetOptimizationSettings.component.html'), // eslint-disable-line max-len
    controller: function () {
        var $ctrl = this;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };
    },
});
