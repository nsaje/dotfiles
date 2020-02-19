angular
    .module('one.common')
    .component('zemEnvironmentDeviceTargetingSettings', {
        bindings: {
            targetEnvironments: '<',
            onUpdate: '&',
        },
        template: require('./zemEnvironmentDeviceTargetingSettings.component.html'), // eslint-disable-line max-len
        controller: function() {
            var $ctrl = this;

            $ctrl.environments = [];
            $ctrl.updateEnvironments = updateEnvironments;

            $ctrl.$onInit = function() {};

            $ctrl.$onChanges = function(changes) {
                if (changes.targetEnvironments && $ctrl.targetEnvironments) {
                    $ctrl.environments = angular.copy($ctrl.targetEnvironments);
                }
            };

            function updateEnvironments() {
                $ctrl.onUpdate({$event: $ctrl.environments});
            }
        },
    });
