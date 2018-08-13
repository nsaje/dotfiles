angular.module('one.widgets').component('zemPublisherGroupTargeting', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemPublisherGroupTargeting.component.html'), // eslint-disable-line max-len
    controller: function(
        zemPermissions,
        zemPublisherGroupsEndpoint,
        zemPublisherGroupTargetingService
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.texts = {
            selectedIncludedTitle: 'Whitelisted publisher groups',
            selectedExcludedTitle: 'Blacklisted publisher groups',
            selectTargetingButton: 'Add publisher group',
            noChoice: 'No available publisher groups',
            toggleTargetingEditSection: 'Enable publisher targeting',
        };
        $ctrl.publisherGroups = null;

        $ctrl.addIncluded = addIncluded;
        $ctrl.addExcluded = addExcluded;
        $ctrl.removeTargeting = removeTargeting;

        $ctrl.$onInit = function() {
            $ctrl.api.register({});
        };

        $ctrl.$onChanges = function() {
            if ($ctrl.entity) {
                if (
                    $ctrl.publisherGroups &&
                    $ctrl.previousEntityId === $ctrl.entity.id
                ) {
                    $ctrl.targetings = getPublisherGroups();
                } else {
                    $ctrl.publisherGroups = null;
                    zemPublisherGroupTargetingService
                        .getPublisherGroups($ctrl.entity)
                        .then(function(data) {
                            $ctrl.publisherGroups = data;
                            $ctrl.targetings = getPublisherGroups();
                        });
                }
                $ctrl.previousEntityId = $ctrl.entity.id;
            }
        };

        function addIncluded(targeting) {
            if (!$ctrl.entity.settings.whitelistPublisherGroups) {
                $ctrl.entity.settings.whitelistPublisherGroups = [];
            }
            $ctrl.entity.settings.whitelistPublisherGroups.push(targeting.id);
            $ctrl.targetings = getPublisherGroups();
        }

        function addExcluded(targeting) {
            if (!$ctrl.entity.settings.blacklistPublisherGroups) {
                $ctrl.entity.settings.blacklistPublisherGroups = [];
            }
            $ctrl.entity.settings.blacklistPublisherGroups.push(targeting.id);
            $ctrl.targetings = getPublisherGroups();
        }

        function removeTargeting(targeting) {
            var index = $ctrl.entity.settings.whitelistPublisherGroups.indexOf(
                targeting.id
            );
            if (index !== -1) {
                $ctrl.entity.settings.whitelistPublisherGroups = $ctrl.entity.settings.whitelistPublisherGroups
                    .slice(0, index)
                    .concat(
                        $ctrl.entity.settings.whitelistPublisherGroups.slice(
                            index + 1
                        )
                    );
            }

            index = $ctrl.entity.settings.blacklistPublisherGroups.indexOf(
                targeting.id
            );
            if (index !== -1) {
                $ctrl.entity.settings.blacklistPublisherGroups = $ctrl.entity.settings.blacklistPublisherGroups
                    .slice(0, index)
                    .concat(
                        $ctrl.entity.settings.blacklistPublisherGroups.slice(
                            index + 1
                        )
                    );
            }

            $ctrl.targetings = getPublisherGroups();
        }

        function getPublisherGroups() {
            var targetings = {
                included: [],
                excluded: [],
                notSelected: [],
            };
            if (!$ctrl.entity || $ctrl.publisherGroups === null)
                return targetings;

            var groups = $ctrl.publisherGroups.slice();
            groups.sort(function(opt1, opt2) {
                return opt1.name.localeCompare(opt2.name);
            });

            groups.forEach(function(pg) {
                if (
                    $ctrl.entity.settings.whitelistPublisherGroups.indexOf(
                        pg.id
                    ) !== -1
                ) {
                    targetings.included.push(getTargetingEntity(pg));
                } else if (
                    $ctrl.entity.settings.blacklistPublisherGroups.indexOf(
                        pg.id
                    ) !== -1
                ) {
                    targetings.excluded.push(getTargetingEntity(pg));
                } else {
                    targetings.notSelected.push(getTargetingEntity(pg));
                }
            });

            return targetings;
        }

        function getTargetingEntity(pg) {
            return {
                section: 'Publisher groups',
                id: pg.id,
                archived: false,
                name: pg.name,
                title: pg.name,
            };
        }
    },
});
