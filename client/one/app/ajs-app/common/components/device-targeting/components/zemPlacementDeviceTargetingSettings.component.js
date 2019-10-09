angular.module('one.common').component('zemPlacementDeviceTargetingSettings', {
    bindings: {
        targetPlacements: '<',
        onUpdate: '&',
    },
    template: require('./zemPlacementDeviceTargetingSettings.component.html'), // eslint-disable-line max-len
    controller: function() {
        var $ctrl = this;

        $ctrl.placements = [];
        $ctrl.updatePlacements = updatePlacements;

        $ctrl.$onInit = function() {};

        $ctrl.$onChanges = function(changes) {
            if (changes.targetPlacements && $ctrl.targetPlacements) {
                $ctrl.placements = angular.copy($ctrl.targetPlacements);
            }
        };

        function updatePlacements() {
            $ctrl.onUpdate({$event: $ctrl.placements});
        }
    },
});
