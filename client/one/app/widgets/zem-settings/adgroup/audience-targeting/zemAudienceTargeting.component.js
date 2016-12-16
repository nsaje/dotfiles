angular.module('one.widgets').component('zemAudienceTargeting', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/adgroup/audience-targeting/zemAudienceTargeting.component.html',  // eslint-disable-line max-len
    controller: function (config, zemPermissions) {
        var AD_GROUP_TARGETING = 'adGroupTargeting';
        var AUDIENCE_TARGETING = 'audienceTargeting';

        var $ctrl = this;

        $ctrl.config = config;
        $ctrl.retargetingEnabled = false;
        $ctrl.getTargetingWarningMessage = getTargetingWarningMessage;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        // inclusion component
        $ctrl.allTargetings = [];
        $ctrl.texts = {
            selectedIncludedTitle: 'Included Audiences',
            selectedExcludedTitle: 'Excluded Audiences',
            selectTargetingButton: 'Add Custom Audience',
            noChoice: 'No available ad group or audience',
        };
        $ctrl.addTargeting = addTargeting;
        $ctrl.removeTargeting = removeTargeting;

        $ctrl.$onInit = function () {
            $ctrl.api.register({});
        };

        $ctrl.$onChanges = function () {
            $ctrl.retargetingEnabled = isRetargetingEnabled();
            $ctrl.allTargetings = getAllAudiencesAndAdGroups();
        };

        function isRetargetingEnabled () {
            if (!$ctrl.entity) return false;
            var settings = $ctrl.entity.settings;
            if (!$ctrl.hasPermission('zemauth.can_target_custom_audiences')
                && settings.retargetingAdGroups && !!settings.retargetingAdGroups.length) {
                return true;
            }

            if ((settings.retargetingAdGroups && !!settings.retargetingAdGroups.length) ||
                (settings.exclusionRetargetingAdGroups && !!settings.exclusionRetargetingAdGroups.length) ||
                (settings.audienceTargeting && !!settings.audienceTargeting.length) ||
                (settings.exclusionAudienceTargeting && !!settings.exclusionAudienceTargeting.length)) {
                return true;
            }

            return false;
        }

        function getTargetingWarningMessage () {
            if ($ctrl.entity.warnings && $ctrl.entity.warnings.retargeting !== undefined) {
                var text = 'You have some active media sources that ' +
                        'don\'t support retargeting. ' +
                        'To start using it please disable/pause these media sources:';
                var sourcesText = $ctrl.entity.warnings.retargeting.sources.join(', ');

                return text + ' ' + sourcesText + '.';
            }
            return null;
        }

        function addTargeting (targeting) {
            if (targeting.type === AD_GROUP_TARGETING) {
                addTargetingToCollection(targeting, 'retargetingAdGroups', 'exclusionRetargetingAdGroups');
            } else if (targeting.type === AUDIENCE_TARGETING) {
                addTargetingToCollection(targeting, 'audienceTargeting', 'exclusionAudienceTargeting');
            }
            $ctrl.retargetingEnabled = isRetargetingEnabled();
        }

        function addTargetingToCollection (targeting, inclusionCollectionName, exclusionCollectionName) {
            if (targeting.included) {
                if (!$ctrl.entity.settings[inclusionCollectionName]) {
                    $ctrl.entity.settings[inclusionCollectionName] = [];
                }
                $ctrl.entity.settings[inclusionCollectionName].push(targeting.id);
            } else if (targeting.excluded) {
                if (!$ctrl.entity.settings[exclusionCollectionName]) {
                    $ctrl.entity.settings[exclusionCollectionName] = [];
                }
                $ctrl.entity.settings[exclusionCollectionName].push(targeting.id);
            }
        }

        function removeTargeting (targeting) {
            if (targeting.type === AD_GROUP_TARGETING) {
                removeTargetingFromCollection(targeting, 'retargetingAdGroups', 'exclusionRetargetingAdGroups');
            } else if (targeting.type === AUDIENCE_TARGETING) {
                removeTargetingFromCollection(targeting, 'audienceTargeting', 'exclusionAudienceTargeting');
            }
            $ctrl.retargetingEnabled = isRetargetingEnabled();
        }

        function removeTargetingFromCollection (targeting, inclusionCollectionName, exclusionCollectionName) {
            var index = -1;
            if ($ctrl.entity.settings[inclusionCollectionName]) {
                index = $ctrl.entity.settings[inclusionCollectionName].indexOf(targeting.id);
                if (index >= 0) {
                    $ctrl.entity.settings[inclusionCollectionName].splice(index, 1);
                }
            }

            if ($ctrl.entity.settings[exclusionCollectionName]) {
                index = $ctrl.entity.settings[exclusionCollectionName].indexOf(targeting.id);
                if (index >= 0) {
                    $ctrl.entity.settings[exclusionCollectionName].splice(index, 1);
                }
            }
        }

        function getAllAudiencesAndAdGroups () {
            var audiences = getAllAudiences(),
                adGroups = getAllAdGroups();

            return audiences.concat(adGroups);
        }

        function getAllAudiences () {
            var included, excluded, i, audience = null, result = [];

            if (!$ctrl.entity) return result;

            var availableAudiences = $ctrl.entity.audiences;
            if (!availableAudiences) return result;

            for (i = 0; i < availableAudiences.length; i++) {
                audience = availableAudiences[i];
                included = $ctrl.entity.settings.audienceTargeting.indexOf(audience.id) >= 0;
                excluded = $ctrl.entity.settings.exclusionAudienceTargeting.indexOf(audience.id) >= 0;

                if (included || excluded || !audience.archived) {
                    result.push(getTargetingEntity(AUDIENCE_TARGETING, audience, included, excluded));
                }
            }

            return result;
        }

        function getAllAdGroups () {
            var included, excluded, i, adGroup = null, result = [];

            if (!$ctrl.entity) return result;

            var availableAdGroups = $ctrl.entity.retargetableAdGroups;
            if (!availableAdGroups) return result;

            for (i = 0; i < availableAdGroups.length; i++) {
                adGroup = availableAdGroups[i];
                included = $ctrl.entity.settings.retargetingAdGroups.indexOf(adGroup.id) >= 0;
                excluded = $ctrl.entity.settings.exclusionRetargetingAdGroups.indexOf(adGroup.id) >= 0;

                // it is not the same ad group
                if (adGroup.id !== parseInt($ctrl.entity.settings.id, 10)
                    && (included || excluded || !adGroup.archived)) {

                    result.push(getTargetingEntity(AD_GROUP_TARGETING, adGroup, included, excluded));
                }
            }

            return result;
        }

        function getTargetingEntity (type, targeting, included, excluded) {
            if (type === AD_GROUP_TARGETING) {
                return {
                    type: AD_GROUP_TARGETING,
                    section: targeting.campaignName,
                    id: targeting.id,
                    archived: targeting.archived,
                    name: targeting.name + ' [' + targeting.id + ']',
                    title: 'Ad group "' + targeting.name + '" [' + targeting.id + ']',
                    included: included,
                    excluded: excluded,
                };
            }

            return {
                type: AUDIENCE_TARGETING,
                section: 'Custom Audiences',
                id: targeting.id,
                archived: targeting.archived,
                name: targeting.name + ' [' + targeting.id + ']',
                title: 'Audience "' + targeting.name + '" [' + targeting.id + ']',
                included: included,
                excluded: excluded,
            };
        }
    }
});