angular.module('one.widgets').component('zemInterestTargeting', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/interest-targeting/zemInterestTargeting.component.html',  // eslint-disable-line max-len
    controller: function (zemPermissions) {
        var $ctrl = this;

        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.constants = constants;

        $ctrl.texts = {
            selectedIncludedTitle: 'Included Interests',
            selectedExcludedTitle: 'Excluded Interests',
            selectTargetingButton: 'Add Interest',
            noChoice: 'No available interests',
            include: 'Include',
            exclude: 'Exclude',
        };
        $ctrl.allTargetings = [];
        $ctrl.addTargeting = addTargeting;
        $ctrl.removeTargeting = removeTargeting;

        $ctrl.$onInit = function () {
            $ctrl.api.register({});
        };

        $ctrl.$onChanges = function () {
            $ctrl.allTargetings = getInterests();
        };

        function addTargeting (targeting) {
            if (targeting.included) {
                if (!$ctrl.entity.settings.interestTargeting) {
                    $ctrl.entity.settings.interestTargeting = [];
                }
                $ctrl.entity.settings.interestTargeting.push(targeting.id);
            }

            if (targeting.excluded) {
                if (!$ctrl.entity.settings.exclusionInterestTargeting) {
                    $ctrl.entity.settings.exclusionInterestTargeting = [];
                }
                $ctrl.entity.settings.exclusionInterestTargeting.push(targeting.id);
            }
        }

        function removeTargeting (targeting) {
            var id = targeting.id, index = -1;

            index = $ctrl.entity.settings.interestTargeting.indexOf(id);
            if (index >= 0) {
                $ctrl.entity.settings.interestTargeting.splice(index, 1);
            }

            index = $ctrl.entity.settings.exclusionInterestTargeting.indexOf(id);
            if (index >= 0) {
                $ctrl.entity.settings.exclusionInterestTargeting.splice(index, 1);
            }
        }

        function getInterests () {
            var interests = options.interests.slice(),
                included, excluded, result = [];

            if (!$ctrl.entity) {
                return result;
            }
            interests.sort(function (opt1, opt2) {
                return opt1.name.localeCompare(opt2.name);
            });
            interests.forEach(function (interest) {
                included = $ctrl.entity.settings.interestTargeting.indexOf(interest.value) >= 0;
                excluded = $ctrl.entity.settings.exclusionInterestTargeting.indexOf(interest.value) >= 0;

                if (included || excluded || !interest.internal) {
                    result.push(getTargetingEntity(interest, included, excluded));
                }
            });

            return result;
        }

        function getTargetingEntity (interest, included, excluded) {
            return {
                section: 'Interests',
                id: interest.value,
                archived: interest.internal,
                name: interest.name,
                title: interest.name,
                included: included,
                excluded: excluded,
            };
        }
    }
});
