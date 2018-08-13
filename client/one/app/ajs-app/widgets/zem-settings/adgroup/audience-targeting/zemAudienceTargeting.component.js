angular.module('one.widgets').component('zemAudienceTargeting', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemAudienceTargeting.component.html'), // eslint-disable-line max-len
    controller: function(config, zemPermissions) {
        var AD_GROUP_TARGETING = 'adGroupTargeting';
        var AUDIENCE_TARGETING = 'audienceTargeting';

        var $ctrl = this;

        $ctrl.config = config;
        $ctrl.getTargetingWarningMessage = getTargetingWarningMessage;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        // inclusion component
        $ctrl.texts = {
            selectedIncludedTitle: 'Included Audiences',
            selectedExcludedTitle: 'Excluded Audiences',
            selectTargetingButton: 'Add Custom Audience',
            noChoice: 'No available ad group or audience',
            toggleTargetingEditSection: 'Enable audience targeting',
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

        function getTargetingWarningMessage() {
            if (
                $ctrl.entity.warnings &&
                $ctrl.entity.warnings.retargeting !== undefined
            ) {
                var text =
                    'You have some active media sources that ' +
                    "don't support retargeting. " +
                    'To start using it please disable/pause these media sources:';
                var sourcesText = $ctrl.entity.warnings.retargeting.sources.join(
                    ', '
                );

                return text + ' ' + sourcesText + '.';
            }
            return null;
        }

        function addIncluded(targeting) {
            if (targeting.type === AD_GROUP_TARGETING) {
                addTargetingToCollection(targeting, 'retargetingAdGroups');
            } else if (targeting.type === AUDIENCE_TARGETING) {
                addTargetingToCollection(targeting, 'audienceTargeting');
            }
            $ctrl.targetings = getTargetings();
        }

        function addExcluded(targeting) {
            if (targeting.type === AD_GROUP_TARGETING) {
                addTargetingToCollection(
                    targeting,
                    'exclusionRetargetingAdGroups'
                );
            } else if (targeting.type === AUDIENCE_TARGETING) {
                addTargetingToCollection(
                    targeting,
                    'exclusionAudienceTargeting'
                );
            }
            $ctrl.targetings = getTargetings();
        }

        function addTargetingToCollection(targeting, collectionName) {
            if (!$ctrl.entity.settings[collectionName]) {
                $ctrl.entity.settings[collectionName] = [];
            }
            $ctrl.entity.settings[collectionName].push(targeting.id);
        }

        function removeTargeting(targeting) {
            if (targeting.type === AD_GROUP_TARGETING) {
                removeTargetingFromCollection(
                    targeting,
                    'retargetingAdGroups',
                    'exclusionRetargetingAdGroups'
                );
            } else if (targeting.type === AUDIENCE_TARGETING) {
                removeTargetingFromCollection(
                    targeting,
                    'audienceTargeting',
                    'exclusionAudienceTargeting'
                );
            }
            $ctrl.targetings = getTargetings();
        }

        function removeTargetingFromCollection(
            targeting,
            inclusionCollectionName,
            exclusionCollectionName
        ) {
            var index = -1;
            if ($ctrl.entity.settings[inclusionCollectionName]) {
                index = $ctrl.entity.settings[inclusionCollectionName].indexOf(
                    targeting.id
                );
                if (index !== -1) {
                    $ctrl.entity.settings[
                        inclusionCollectionName
                    ] = $ctrl.entity.settings[inclusionCollectionName]
                        .slice(0, index)
                        .concat(
                            $ctrl.entity.settings[
                                inclusionCollectionName
                            ].slice(index + 1)
                        );
                }
            }

            if ($ctrl.entity.settings[exclusionCollectionName]) {
                index = $ctrl.entity.settings[exclusionCollectionName].indexOf(
                    targeting.id
                );
                if (index !== -1) {
                    $ctrl.entity.settings[
                        exclusionCollectionName
                    ] = $ctrl.entity.settings[exclusionCollectionName]
                        .slice(0, index)
                        .concat(
                            $ctrl.entity.settings[
                                exclusionCollectionName
                            ].slice(index + 1)
                        );
                }
            }

            $ctrl.targetings = getTargetings();
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

            if (!$ctrl.entity) return audiences;

            var availableAudiences = $ctrl.entity.audiences;
            if (!availableAudiences) return audiences;

            availableAudiences.forEach(function(audience) {
                if (
                    $ctrl.entity.settings.audienceTargeting.indexOf(
                        audience.id
                    ) !== -1
                ) {
                    audiences.included.push(
                        getTargetingEntity(AUDIENCE_TARGETING, audience)
                    );
                } else if (
                    $ctrl.entity.settings.exclusionAudienceTargeting.indexOf(
                        audience.id
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

            if (!$ctrl.entity) return adGroups;

            var availableAdGroups = $ctrl.entity.retargetableAdGroups;
            if (!availableAdGroups) return adGroups;

            availableAdGroups.forEach(function(adGroup) {
                if (adGroup.id === parseInt($ctrl.entity.settings.id, 10))
                    return;

                if (
                    $ctrl.entity.settings.retargetingAdGroups.indexOf(
                        adGroup.id
                    ) !== -1
                ) {
                    adGroups.included.push(
                        getTargetingEntity(AD_GROUP_TARGETING, adGroup)
                    );
                } else if (
                    $ctrl.entity.settings.exclusionRetargetingAdGroups.indexOf(
                        adGroup.id
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
                    id: targeting.id,
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
                id: targeting.id,
                archived: targeting.archived,
                name: targeting.name + ' [' + targeting.id + ']',
                title:
                    'Audience "' + targeting.name + '" [' + targeting.id + ']',
            };
        }
    },
});
