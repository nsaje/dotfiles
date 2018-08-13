angular.module('one.widgets').component('zemPlacementDeviceTargetingSettings', {
    bindings: {
        stateService: '<',
    },
    template: require('./zemPlacementDeviceTargetingSettings.component.html'), // eslint-disable-line max-len
    controller: function() {
        var $ctrl = this;

        $ctrl.$onInit = function() {};

        $ctrl.$onChanges = function(changes) {
            if (changes.stateService && $ctrl.stateService) {
                $ctrl.state = $ctrl.stateService.getState();
            }
        };
    },
});
