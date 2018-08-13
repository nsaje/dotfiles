angular.module('one').component('zemCampaignLauncherTargeting', {
    bindings: {
        stateService: '=',
    },
    template: require('./zemCampaignLauncherTargeting.component.html'),
    controller: function() {
        var $ctrl = this;

        $ctrl.$onInit = function() {
            $ctrl.state = $ctrl.stateService.getState();
            initTargetingWidgets();
        };

        function initTargetingWidgets() {
            $ctrl.entity = {
                settings: $ctrl.state.fields,
            };
        }
    },
});
