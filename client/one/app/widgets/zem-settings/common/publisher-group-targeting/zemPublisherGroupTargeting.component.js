angular.module('one.widgets').component('zemPublisherGroupTargeting', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/common/publisher-group-targeting/zemPublisherGroupTargeting.component.html',  // eslint-disable-line max-len
    controller: function (zemPermissions, zemPublisherGroupsEndpoint, zemPublisherGroupTargetingService) {  // eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.texts = {
            selectedIncludedTitle: 'Whitelisted publisher groups',
            selectedExcludedTitle: 'Blacklisted publisher groups',
            selectTargetingButton: 'Blacklist publisher group',
            noChoice: 'No available publisher groups',
        };
        $ctrl.publisherGroups = null;

        $ctrl.allTargetings = [];
        $ctrl.addTargeting = addTargeting;
        $ctrl.removeTargeting = removeTargeting;

        $ctrl.$onInit = function () {
            $ctrl.api.register({});
        };

        $ctrl.$onChanges = function () {
            if ($ctrl.entity) {
                if ($ctrl.publisherGroups && $ctrl.previousEntityId === $ctrl.entity.id) {
                    $ctrl.allTargetings = getPublisherGroups();
                } else {
                    $ctrl.publisherGroups = null;
                    zemPublisherGroupTargetingService.getPublisherGroups($ctrl.entity).then(function (data) {
                        $ctrl.publisherGroups = data;
                        $ctrl.allTargetings = getPublisherGroups();
                    });
                }
                $ctrl.previousEntityId = $ctrl.entity.id;
            }
        };

        function addTargeting (targeting) {
            if (targeting.included) {
                if (!$ctrl.entity.settings.whitelistPublisherGroups) {
                    $ctrl.entity.settings.whitelistPublisherGroups = [];
                }
                $ctrl.entity.settings.whitelistPublisherGroups.push(targeting.id);
            }

            if (targeting.excluded) {
                if (!$ctrl.entity.settings.blacklistPublisherGroups) {
                    $ctrl.entity.settings.blacklistPublisherGroups = [];
                }
                $ctrl.entity.settings.blacklistPublisherGroups.push(targeting.id);
            }
        }

        function removeTargeting (targeting) {
            var index = -1;

            index = $ctrl.entity.settings.whitelistPublisherGroups.indexOf(targeting.id);
            if (index >= 0) {
                $ctrl.entity.settings.whitelistPublisherGroups.splice(index, 1);
            }

            index = $ctrl.entity.settings.blacklistPublisherGroups.indexOf(targeting.id);
            if (index >= 0) {
                $ctrl.entity.settings.blacklistPublisherGroups.splice(index, 1);
            }
        }

        function getPublisherGroups () {
            if ($ctrl.publisherGroups === null) return;

            var groups = $ctrl.publisherGroups.slice(), result = [];

            if (!$ctrl.entity) {
                return result;
            }
            groups.sort(function (opt1, opt2) {
                return opt1.name.localeCompare(opt2.name);
            });

            groups.forEach(function (pg) {
                var included = $ctrl.entity.settings.whitelistPublisherGroups.indexOf(pg.id) >= 0,
                    excluded = $ctrl.entity.settings.blacklistPublisherGroups.indexOf(pg.id) >= 0;
                result.push(getTargetingEntity(pg, included, excluded));
            });

            return result;
        }

        function getTargetingEntity (pg, included, excluded) {
            return {
                section: 'Publisher groups',
                id: pg.id,
                archived: false,
                name: pg.name,
                title: pg.name,
                included: included,
                excluded: excluded,
            };
        }
    }
});