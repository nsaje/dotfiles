require('./zemPublisherGroupTargeting.component.less');

angular.module('one.common').component('zemPublisherGroupTargeting', {
    bindings: {
        accountId: '<',
        whitelistedPublisherGroups: '<',
        blacklistedPublisherGroups: '<',
        whitelistedPublisherGroupsErrors: '<',
        blacklistedPublisherGroupsErrors: '<',
        isDisabled: '<',
        onUpdate: '&',
    },
    template: require('./zemPublisherGroupTargeting.component.html'), // eslint-disable-line max-len
    controller: function(zemPublisherGroupTargetingEndpoint) {
        var $ctrl = this;

        $ctrl.texts = {
            selectTargetingButton: 'Add publisher group',
            noChoice: 'No available publisher groups',
            toggleTargetingEditSection: 'Enable publisher targeting',
            selectedIncludedTitle: 'Whitelisted publisher & placements list',
            selectedExcludedTitle: 'Blacklisted publisher & placements list',
            $selectTargetingButton: 'Select list',
        };
        $ctrl.accountPublisherGroups = null;

        $ctrl.addIncluded = addIncluded;
        $ctrl.addExcluded = addExcluded;
        $ctrl.removeTargeting = removeTargeting;

        $ctrl.$onChanges = function(changes) {
            if (
                changes.whitelistedPublisherGroups ||
                changes.blacklistedPublisherGroups
            ) {
                $ctrl.targetings = generateTargetings(
                    $ctrl.accountPublisherGroups,
                    $ctrl.whitelistedPublisherGroups,
                    $ctrl.blacklistedPublisherGroups
                );
            }

            if (changes.accountId) {
                $ctrl.accountPublisherGroups = null;
                if ($ctrl.accountId) {
                    zemPublisherGroupTargetingEndpoint
                        .list($ctrl.accountId, null, true)
                        .then(function(data) {
                            $ctrl.accountPublisherGroups = data;
                            $ctrl.targetings = generateTargetings(
                                $ctrl.accountPublisherGroups,
                                $ctrl.whitelistedPublisherGroups,
                                $ctrl.blacklistedPublisherGroups
                            );
                        });
                }
            }
        };

        function addIncluded(targeting) {
            var updatedWhitelistedPublisherGroups = angular.copy(
                $ctrl.whitelistedPublisherGroups || []
            );
            updatedWhitelistedPublisherGroups.push(targeting.id);
            propagateUpdate({
                whitelistedPublisherGroups: updatedWhitelistedPublisherGroups,
            });
        }

        function addExcluded(targeting) {
            var updatedBlacklistedPublisherGroups = angular.copy(
                $ctrl.blacklistedPublisherGroups || []
            );
            updatedBlacklistedPublisherGroups.push(targeting.id);
            propagateUpdate({
                blacklistedPublisherGroups: updatedBlacklistedPublisherGroups,
            });
        }

        function removeTargeting(targeting) {
            var updatedWhitelistedPublisherGroups;
            var updatedBlacklistedPublisherGroups;

            var index = $ctrl.whitelistedPublisherGroups.indexOf(targeting.id);
            if (index !== -1) {
                updatedWhitelistedPublisherGroups = angular.copy(
                    $ctrl.whitelistedPublisherGroups
                );
                updatedWhitelistedPublisherGroups.splice(index, 1);
            }

            index = $ctrl.blacklistedPublisherGroups.indexOf(targeting.id);
            if (index !== -1) {
                updatedBlacklistedPublisherGroups = angular.copy(
                    $ctrl.blacklistedPublisherGroups
                );
                updatedBlacklistedPublisherGroups.splice(index, 1);
            }

            if (
                updatedWhitelistedPublisherGroups ||
                updatedBlacklistedPublisherGroups
            ) {
                propagateUpdate({
                    whitelistedPublisherGroups: updatedWhitelistedPublisherGroups,
                    blacklistedPublisherGroups: updatedBlacklistedPublisherGroups,
                });
            }
        }

        function propagateUpdate(newTargeting) {
            $ctrl.onUpdate({
                $event: newTargeting,
            });
        }

        function generateTargetings(
            accountPublisherGroups,
            whitelistedPublisherGroups,
            blacklistedPublisherGroups
        ) {
            var targetings = {
                included: [],
                excluded: [],
                notSelected: [],
            };
            if (accountPublisherGroups === null) {
                return targetings;
            }

            var sortedAccountPublisherGroups = accountPublisherGroups
                .slice()
                .sort(function(opt1, opt2) {
                    return opt1.name.localeCompare(opt2.name);
                });

            sortedAccountPublisherGroups.forEach(function(group) {
                if (
                    (whitelistedPublisherGroups || []).indexOf(group.id) !== -1
                ) {
                    targetings.included.push(
                        generatePublisherGroupObject(group)
                    );
                } else if (
                    (blacklistedPublisherGroups || []).indexOf(group.id) !== -1
                ) {
                    targetings.excluded.push(
                        generatePublisherGroupObject(group)
                    );
                } else {
                    targetings.notSelected.push(
                        generatePublisherGroupObject(group)
                    );
                }
            });

            return targetings;
        }

        function generatePublisherGroupObject(pg) {
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
