angular.module('one.widgets').component('zemOsDeviceTargetingSettings', {
    bindings: {
        stateService: '<',
    },
    template: require('./zemOsDeviceTargetingSettings.component.html'), // eslint-disable-line max-len
    controller: function(zemDeviceTargetingConstants) {
        var $ctrl = this;
        $ctrl.getAvailableOptions = getAvailableOptions;

        $ctrl.$onInit = function() {};

        $ctrl.$onChanges = function(changes) {
            if (changes.stateService && $ctrl.stateService) {
                $ctrl.state = $ctrl.stateService.getState();
                $ctrl.stateService.onUpdate(update);
                update();
            }
        };

        function update() {
            $ctrl.availableOptions = getAvailableOptions();
        }

        function getAvailableOptions() {
            return zemDeviceTargetingConstants.OPERATING_SYSTEMS.filter(
                function(option) {
                    // Remove already added options
                    return (
                        $ctrl.state.operatingSystems.filter(function(
                            operatingSystem
                        ) {
                            return option.value === operatingSystem.value;
                        }).length === 0
                    );
                }
            ).filter(function(option) {
                // Filter based on device compatibility
                return (
                    $ctrl.state.devices.filter(function(device) {
                        if (!device.checked) return false;
                        return option.devices.indexOf(device.value) >= 0;
                    }).length > 0
                );
            });
        }
    },
});
