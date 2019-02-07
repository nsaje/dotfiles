angular.module('one').component('zemCampaignLauncherTargeting', {
    bindings: {
        stateService: '=',
    },
    template: require('./zemCampaignLauncherTargeting.component.html'),
    controller: function() {
        var $ctrl = this;

        $ctrl.updateGeoTargeting = updateGeoTargeting;
        $ctrl.updateDeviceTargeting = updateDeviceTargeting;

        $ctrl.$onInit = function() {
            $ctrl.state = $ctrl.stateService.getState();
        };

        function updateGeoTargeting($event) {
            if ($event.includedLocations) {
                $ctrl.state.fields.targetRegions = $event.includedLocations;
            }
            if ($event.excludedLocations) {
                $ctrl.state.fields.exclusionTargetRegions =
                    $event.excludedLocations;
            }
        }

        function updateDeviceTargeting($event) {
            $ctrl.state.fields.targetDevices = $event.targetDevices;
            $ctrl.state.fields.targetPlacements = $event.targetPlacements;
            $ctrl.state.fields.targetOs = $event.targetOs;
        }
    },
});
