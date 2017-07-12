angular.module('one').component('zemCampaignLauncherReview', {
    bindings: {
        stateService: '=',
    },
    template: require('./zemCampaignLauncherReview.component.html'), // eslint-disable-line max-len
    controller: function () {
        var $ctrl = this;

        $ctrl.goToStep = $ctrl.stateService.goToStep;

        $ctrl.$onInit = function () {
            $ctrl.state = $ctrl.stateService.getState();
        };
    },
});
