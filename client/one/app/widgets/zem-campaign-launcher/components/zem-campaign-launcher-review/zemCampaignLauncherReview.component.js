angular.module('one').component('zemCampaignLauncherReview', {
    bindings: {
        stateService: '=',
    },
    templateUrl: '/app/widgets/zem-campaign-launcher/components/zem-campaign-launcher-review/zemCampaignLauncherReview.component.html', // eslint-disable-line max-len
    controller: function () {
        var $ctrl = this;

        $ctrl.goToStep = $ctrl.stateService.goToStep;

        $ctrl.$onInit = function () {
            $ctrl.state = $ctrl.stateService.getState();
        };
    },
});
