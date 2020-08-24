angular.module('one.common').component('zemRetargeting', {
    bindings: {
        entityId: '<',
        retargetableAudiences: '<',
        retargetableAdGroups: '<',
        includedAudiences: '<',
        excludedAudiences: '<',
        includedAdGroups: '<',
        excludedAdGroups: '<',
        includedAudiencesErrors: '<',
        excludedAudiencesErrors: '<',
        includedAdGroupsErrors: '<',
        excludedAdGroupsErrors: '<',
        isDisabled: '<',
        warnings: '<',
        onUpdate: '&',
    },
    template: require('./zemRetargeting.component.html'),
    controller: function(config, zemAuthStore) {
        var AD_GROUP_TARGETING = 'adGroupTargeting';
        var AUDIENCE_TARGETING = 'audienceTargeting';

        var $ctrl = this;

        $ctrl.config = config;
        $ctrl.hasPermission = zemAuthStore.hasPermission.bind(zemAuthStore);
        $ctrl.isPermissionInternal = zemAuthStore.isPermissionInternal.bind(
            zemAuthStore
        );

        $ctrl.texts = {
            selectedIncludedTitle: 'Included Audiences',
            selectedExcludedTitle: 'Excluded Audiences',
            selectTargetingButton: 'Add Custom Audience',
            noChoice: 'No available ad group or audience',
            toggleTargetingEditSection: 'Enable retargeting',
        };
        $ctrl.addIncluded = addIncluded;
        $ctrl.addExcluded = addExcluded;
        $ctrl.removeTargeting = removeTargeting;

        // eslint-disable-next-line complexity
        $ctrl.$onChanges = function(changes) {
            if (
                changes.entityId ||
                changes.retargetableAudiences ||
                changes.retargetableAdGroups ||
                changes.includedAudiences ||
                changes.excludedAudiences ||
                changes.includedAdGroups ||
                changes.excludedAdGroups
            ) {
                $ctrl.targetings = getTargetings();
            }

            if (
                changes.includedAudiencesErrors ||
                changes.excludedAudiencesErrors ||
                changes.includedAdGroupsErrors ||
                changes.excludedAdGroupsErrors
            ) {
                $ctrl.errors = []
                    .concat($ctrl.includedAudiencesErrors || [])
                    .concat($ctrl.excludedAudiencesErrors || [])
                    .concat($ctrl.includedAdGroupsErrors || [])
                    .concat($ctrl.excludedAdGroupsErrors || []);
            }

            if (changes.warnings) {
                $ctrl.warningMessage = getTargetingWarningMessage(
                    $ctrl.warnings
                );
            }
        };

        function getTargetingWarningMessage(warnings) {
            if (warnings && warnings.sources && warnings.sources.length > 0) {
                var text =
                    "The following sources don't support retargeting and will be " +
                    'automatically paused in this ad group if you enable this setting:';
                var sourcesText = warnings.sources.join(', ');

                return text + ' ' + sourcesText + '.';
            }
            return null;
        }

        function addIncluded(targeting) {
            if (targeting.type === AUDIENCE_TARGETING) {
                addIncludedAudience(targeting);
            } else if (targeting.type === AD_GROUP_TARGETING) {
                addIncludedAdGroup(targeting);
            }
        }

        function addExcluded(targeting) {
            if (targeting.type === AUDIENCE_TARGETING) {
                addExcludedAudience(targeting);
            } else if (targeting.type === AD_GROUP_TARGETING) {
                addExcludedAdGroup(targeting);
            }
        }

        function addIncludedAudience(targeting) {
            var updatedIncludedAudiences = angular.copy(
                $ctrl.includedAudiences || []
            );
            updatedIncludedAudiences.push(targeting.id);
            propagateUpdate({
                includedAudiences: updatedIncludedAudiences,
            });
        }

        function addIncludedAdGroup(targeting) {
            var updatedIncludedAdGroups = angular.copy(
                $ctrl.includedAdGroups || []
            );
            updatedIncludedAdGroups.push(targeting.id);
            propagateUpdate({
                includedAdGroups: updatedIncludedAdGroups,
            });
        }

        function addExcludedAudience(targeting) {
            var updatedExcludedAudiences = angular.copy(
                $ctrl.excludedAudiences || []
            );
            updatedExcludedAudiences.push(targeting.id);
            propagateUpdate({
                excludedAudiences: updatedExcludedAudiences,
            });
        }

        function addExcludedAdGroup(targeting) {
            var updatedExcludedAdGroups = angular.copy(
                $ctrl.excludedAdGroups || []
            );
            updatedExcludedAdGroups.push(targeting.id);
            propagateUpdate({
                excludedAdGroups: updatedExcludedAdGroups,
            });
        }

        function removeTargeting(targeting) {
            var updatedIncludedAudiences = removeTargetingFromCollection(
                targeting.id,
                $ctrl.includedAudiences
            );
            var updatedExcludedAudiences = removeTargetingFromCollection(
                targeting.id,
                $ctrl.excludedAudiences
            );
            var updatedIncludedAdGroups = removeTargetingFromCollection(
                targeting.id,
                $ctrl.includedAdGroups
            );
            var updatedExcludedAdGroups = removeTargetingFromCollection(
                targeting.id,
                $ctrl.excludedAdGroups
            );

            if (
                updatedIncludedAudiences ||
                updatedExcludedAudiences ||
                updatedIncludedAdGroups ||
                updatedExcludedAdGroups
            ) {
                propagateUpdate({
                    includedAudiences: updatedIncludedAudiences,
                    excludedAudiences: updatedExcludedAudiences,
                    includedAdGroups: updatedIncludedAdGroups,
                    excludedAdGroups: updatedExcludedAdGroups,
                });
            }
        }

        function removeTargetingFromCollection(targetingId, collection) {
            var index = (collection || []).indexOf(targetingId);
            if (index === -1) {
                return;
            }
            var updatedCollection = angular.copy(collection);
            updatedCollection.splice(index, 1);
            return updatedCollection;
        }

        function propagateUpdate(newTargeting) {
            $ctrl.onUpdate({
                $event: newTargeting,
            });
        }

        function getTargetings() {
            var audiences = getAudiences();
            var adGroups = getAdGroups();

            return {
                included: audiences.included.concat(adGroups.included),
                excluded: audiences.excluded.concat(adGroups.excluded),
                notSelected: audiences.notSelected.concat(adGroups.notSelected),
            };
        }

        function getAudiences() {
            var audiences = {
                included: [],
                excluded: [],
                notSelected: [],
            };

            ($ctrl.retargetableAudiences || []).forEach(function(audience) {
                if (
                    ($ctrl.includedAudiences || []).indexOf(
                        parseInt(audience.id, 10)
                    ) !== -1
                ) {
                    audiences.included.push(
                        getTargetingEntity(AUDIENCE_TARGETING, audience)
                    );
                } else if (
                    ($ctrl.excludedAudiences || []).indexOf(
                        parseInt(audience.id, 10)
                    ) !== -1
                ) {
                    audiences.excluded.push(
                        getTargetingEntity(AUDIENCE_TARGETING, audience)
                    );
                } else if (!audience.archived) {
                    audiences.notSelected.push(
                        getTargetingEntity(AUDIENCE_TARGETING, audience)
                    );
                }
            });

            return audiences;
        }

        function getAdGroups() {
            var adGroups = {
                included: [],
                excluded: [],
                notSelected: [],
            };

            ($ctrl.retargetableAdGroups || []).forEach(function(adGroup) {
                if (parseInt(adGroup.id, 10) === parseInt($ctrl.entityId, 10)) {
                    return;
                }

                if (
                    ($ctrl.includedAdGroups || []).indexOf(
                        parseInt(adGroup.id, 10)
                    ) !== -1
                ) {
                    adGroups.included.push(
                        getTargetingEntity(AD_GROUP_TARGETING, adGroup)
                    );
                } else if (
                    ($ctrl.excludedAdGroups || []).indexOf(
                        parseInt(adGroup.id, 10)
                    ) !== -1
                ) {
                    adGroups.excluded.push(
                        getTargetingEntity(AD_GROUP_TARGETING, adGroup)
                    );
                } else if (!adGroup.archived) {
                    adGroups.notSelected.push(
                        getTargetingEntity(AD_GROUP_TARGETING, adGroup)
                    );
                }
            });

            return adGroups;
        }

        function getTargetingEntity(type, targeting) {
            if (type === AD_GROUP_TARGETING) {
                return {
                    type: AD_GROUP_TARGETING,
                    section: targeting.campaignName,
                    id: parseInt(targeting.id, 10),
                    archived: targeting.archived,
                    name: targeting.name + ' [' + targeting.id + ']',
                    title:
                        'Ad group "' +
                        targeting.name +
                        '" [' +
                        targeting.id +
                        ']',
                };
            }

            return {
                type: AUDIENCE_TARGETING,
                section: 'Custom Audiences',
                id: parseInt(targeting.id, 10),
                archived: targeting.archived,
                name: targeting.name + ' [' + targeting.id + ']',
                title:
                    'Audience "' + targeting.name + '" [' + targeting.id + ']',
            };
        }
    },
});
