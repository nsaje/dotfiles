angular.module('one.widgets').component('zemInterestTargeting', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemInterestTargeting.component.html'), // eslint-disable-line max-len
    controller: function(zemPermissions) {
        var $ctrl = this;

        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.constants = constants;

        $ctrl.texts = {
            selectedIncludedTitle: 'Included Interests',
            selectedExcludedTitle: 'Excluded Interests',
            selectTargetingButton: 'Add Interest',
            noChoice: 'No available interests',
            toggleTargetingEditSection: 'Enable interest targeting',
        };
        $ctrl.addIncluded = addIncluded;
        $ctrl.addExcluded = addExcluded;
        $ctrl.removeTargeting = removeTargeting;

        $ctrl.$onInit = function() {
            $ctrl.api.register({});
        };

        $ctrl.$onChanges = function() {
            $ctrl.targetings = getTargetings();
        };

        function addIncluded(targeting) {
            if (!$ctrl.entity.settings.interestTargeting) {
                $ctrl.entity.settings.interestTargeting = [];
            }
            $ctrl.entity.settings.interestTargeting.push(targeting.id);
            $ctrl.targetings = getTargetings();
        }

        function addExcluded(targeting) {
            if (!$ctrl.entity.settings.exclusionInterestTargeting) {
                $ctrl.entity.settings.exclusionInterestTargeting = [];
            }
            $ctrl.entity.settings.exclusionInterestTargeting.push(targeting.id);
            $ctrl.targetings = getTargetings();
        }

        function removeTargeting(targeting) {
            var index = $ctrl.entity.settings.interestTargeting.indexOf(
                targeting.id
            );
            if (index !== -1) {
                $ctrl.entity.settings.interestTargeting = $ctrl.entity.settings.interestTargeting
                    .slice(0, index)
                    .concat(
                        $ctrl.entity.settings.interestTargeting.slice(index + 1)
                    );
            }

            index = $ctrl.entity.settings.exclusionInterestTargeting.indexOf(
                targeting.id
            );
            if (index !== -1) {
                $ctrl.entity.settings.exclusionInterestTargeting = $ctrl.entity.settings.exclusionInterestTargeting
                    .slice(0, index)
                    .concat(
                        $ctrl.entity.settings.exclusionInterestTargeting.slice(
                            index + 1
                        )
                    );
            }

            $ctrl.targetings = getTargetings();
        }

        function getTargetings() {
            var targetings = {
                included: [],
                excluded: [],
                notSelected: [],
            };

            if (!$ctrl.entity) return targetings;

            var interests = options.interests.slice();
            interests.sort(function(opt1, opt2) {
                return opt1.name.localeCompare(opt2.name);
            });
            interests.forEach(function(interest) {
                if (
                    $ctrl.entity.settings.interestTargeting.indexOf(
                        interest.value
                    ) !== -1
                ) {
                    targetings.included.push(getTargetingEntity(interest));
                } else if (
                    $ctrl.entity.settings.exclusionInterestTargeting.indexOf(
                        interest.value
                    ) !== -1
                ) {
                    targetings.excluded.push(getTargetingEntity(interest));
                } else if (!interest.internal) {
                    targetings.notSelected.push(getTargetingEntity(interest));
                }
            });

            return targetings;
        }

        function getTargetingEntity(interest) {
            return {
                section: 'Interests',
                id: interest.value,
                archived: interest.internal,
                name: interest.name,
                title: interest.name,
            };
        }
    },
});
