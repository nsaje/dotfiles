angular.module('one').component('zemCampaignLauncherObjectives', {
    bindings: {
        selectObjective: '&',
    },
    template: require('./zemCampaignLauncherObjectives.component.html'), // eslint-disable-line max-len
    controller: function () {
        var $ctrl = this;

        $ctrl.$onInit = function () {
            $ctrl.campaignObjective = constants.campaignObjective;
        };
    },
});
