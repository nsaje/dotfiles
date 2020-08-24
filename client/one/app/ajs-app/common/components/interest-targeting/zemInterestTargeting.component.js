var interestTargetingConfig = require('../../../../features/entity-manager/components/interest-targeting/interest-targeting.config.ts')
    .INTEREST_TARGETING_CONFIG;

angular.module('one.common').component('zemInterestTargeting', {
    bindings: {
        legacyOptions: '<',
        includedInterests: '<',
        excludedInterests: '<',
        includedInterestsErrors: '<',
        excludedInterestsErrors: '<',
        isDisabled: '<',
        onUpdate: '&',
    },
    template: require('./zemInterestTargeting.component.html'), // eslint-disable-line max-len
    controller: function(zemAuthStore) {
        var $ctrl = this;

        $ctrl.hasPermission = zemAuthStore.hasPermission.bind(zemAuthStore);
        $ctrl.isPermissionInternal = zemAuthStore.isPermissionInternal.bind(
            zemAuthStore
        );

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

        $ctrl.$onChanges = function(changes) {
            if (changes.includedInterests || changes.excludedInterests) {
                $ctrl.targetings = generateTargetings(
                    $ctrl.includedInterests,
                    $ctrl.excludedInterests
                );
            }

            if (
                changes.includedInterestsErrors ||
                changes.excludedInterestsErrors
            ) {
                $ctrl.errors = generateErrors(
                    $ctrl.includedInterestsErrors,
                    $ctrl.excludedInterestsErrors
                );
            }
        };

        function addIncluded(targeting) {
            var updatedIncludedInterests = angular.copy(
                $ctrl.includedInterests || []
            );
            updatedIncludedInterests.push(targeting.id);
            propagateUpdate({
                includedInterests: updatedIncludedInterests,
            });
        }

        function addExcluded(targeting) {
            var updatedExcludedInterests = angular.copy(
                $ctrl.excludedInterests || []
            );
            updatedExcludedInterests.push(targeting.id);
            propagateUpdate({
                excludedInterests: updatedExcludedInterests,
            });
        }

        function removeTargeting(targeting) {
            var updatedIncludedInterests;
            var updatedExcludedInterests;

            var index = $ctrl.includedInterests.indexOf(targeting.id);
            if (index !== -1) {
                updatedIncludedInterests = angular.copy(
                    $ctrl.includedInterests
                );
                updatedIncludedInterests.splice(index, 1);
            }

            index = $ctrl.excludedInterests.indexOf(targeting.id);
            if (index !== -1) {
                updatedExcludedInterests = angular.copy(
                    $ctrl.excludedInterests
                );
                updatedExcludedInterests.splice(index, 1);
            }

            if (updatedIncludedInterests || updatedExcludedInterests) {
                propagateUpdate({
                    includedInterests: updatedIncludedInterests,
                    excludedInterests: updatedExcludedInterests,
                });
            }
        }

        function propagateUpdate(newTargeting) {
            $ctrl.onUpdate({
                $event: newTargeting,
            });
        }

        function generateTargetings(includedInterests, excludedInterests) {
            var targetings = {
                included: [],
                excluded: [],
                notSelected: [],
            };

            var interests;
            if ($ctrl.legacyOptions) {
                interests = $ctrl.legacyOptions.slice();
            } else {
                interests = interestTargetingConfig.interestCategories.slice();
            }

            interests.sort(function(opt1, opt2) {
                return opt1.name.localeCompare(opt2.name);
            });
            interests.forEach(function(interest) {
                if ((includedInterests || []).indexOf(interest.value) !== -1) {
                    targetings.included.push(generateInterestObject(interest));
                } else if (
                    (excludedInterests || []).indexOf(interest.value) !== -1
                ) {
                    targetings.excluded.push(generateInterestObject(interest));
                } else if (!interest.internal) {
                    targetings.notSelected.push(
                        generateInterestObject(interest)
                    );
                }
            });

            return targetings;
        }

        function generateErrors(
            includedInterestsErrors,
            excludedInterestsErrors
        ) {
            return (includedInterestsErrors || []).concat(
                excludedInterestsErrors || []
            );
        }

        function generateInterestObject(interest) {
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
