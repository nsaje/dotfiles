angular.module('one').component('zemCampaignLauncherObjectives', {
    bindings: {
        selectObjective: '&',
    },
    templateUrl: '/app/widgets/zem-campaign-launcher/components/zem-campaign-launcher-objectives/zemCampaignLauncherObjectives.component.html', // eslint-disable-line max-len
    controller: function () {
        var $ctrl = this;

        $ctrl.$onInit = function () {
            $ctrl.campaignObjective = constants.campaignObjective;
        };
    },
});
