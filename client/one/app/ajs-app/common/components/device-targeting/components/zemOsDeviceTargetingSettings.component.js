angular.module('one.common').component('zemOsDeviceTargetingSettings', {
    bindings: {
        targetDevices: '<',
        targetOs: '<',
        onUpdate: '&',
    },
    template: require('./zemOsDeviceTargetingSettings.component.html'), // eslint-disable-line max-len
    controller: function(zemDeviceTargetingConstants) {
        var $ctrl = this;

        $ctrl.operatingSystems = [];
        $ctrl.getAvailableOptions = getAvailableOptions;
        $ctrl.addOperatingSystem = addOperatingSystem;
        $ctrl.updateOperatingSystems = updateOperatingSystems;
        $ctrl.removeOperatingSystem = removeOperatingSystem;

        $ctrl.$onInit = function() {};

        $ctrl.$onChanges = function(changes) {
            if (!$ctrl.targetOs || !$ctrl.targetDevices) {
                return;
            }
            if (changes.targetOs || changes.targetDevices) {
                $ctrl.operatingSystems = angular.copy($ctrl.targetOs);
                $ctrl.availableOptions = getAvailableOptions();
            }
        };

        function getAvailableOptions() {
            return zemDeviceTargetingConstants.OPERATING_SYSTEMS.filter(
                function(option) {
                    // Remove already added options
                    return (
                        $ctrl.operatingSystems.filter(function(
                            operatingSystem
                        ) {
                            return option.value === operatingSystem.value;
                        }).length === 0
                    );
                }
            ).filter(function(option) {
                // Filter based on device compatibility
                return (
                    $ctrl.targetDevices.filter(function(device) {
                        if (!device.checked) return false;
                        return option.devices.indexOf(device.value) >= 0;
                    }).length > 0
                );
            });
        }

        function addOperatingSystem(item) {
            var operatingSystem = angular.copy(item);
            if (operatingSystem.versions) {
                operatingSystem.versions.unshift({
                    value: null,
                    name: ' - ',
                });
                operatingSystem.version = {
                    min: operatingSystem.versions[0],
                    max: operatingSystem.versions[0],
                };
            }
            $ctrl.operatingSystems.push(operatingSystem);
            $ctrl.onUpdate({$event: $ctrl.operatingSystems});
        }

        function updateOperatingSystems() {
            $ctrl.onUpdate({$event: $ctrl.operatingSystems});
        }

        function removeOperatingSystem(item) {
            var idx = $ctrl.operatingSystems.indexOf(item);
            $ctrl.operatingSystems.splice(idx, 1);
            $ctrl.onUpdate({$event: $ctrl.operatingSystems});
        }
    },
});
