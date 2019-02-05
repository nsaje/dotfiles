angular.module('one').component('zemCampaignLauncherTargeting', {
    bindings: {
        stateService: '=',
    },
    template: require('./zemCampaignLauncherTargeting.component.html'),
    controller: function() {
        var $ctrl = this;

        $ctrl.updateGeoTargeting = updateGeoTargeting;

        $ctrl.$onInit = function() {
            $ctrl.state = $ctrl.stateService.getState();
            initTargetingWidgets();
        };

        function initTargetingWidgets() {
            $ctrl.entity = {
                settings: $ctrl.state.fields,
            };
        }

        function updateGeoTargeting(updatedGeoTargeting) {
            if (updatedGeoTargeting.includedLocations) {
                $ctrl.state.fields.targetRegions =
                    updatedGeoTargeting.includedLocations;
            }
            if (updatedGeoTargeting.excludedLocations) {
                $ctrl.state.fields.exclusionTargetRegions =
                    updatedGeoTargeting.excludedLocations;
            }
        }
    },
});
