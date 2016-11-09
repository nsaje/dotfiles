/*globals angular,constants*/
'use strict';

angular.module('one.legacy').component('zemCustomAudiencesTargeting', {
    templateUrl: '/components/zem-custom-audiences-targeting/zemCustomAudiencesTargeting.component.html',
    bindings: {
        currentAdGroupId: '<',
        availableAdGroups: '<',
        availableAudiences: '<',
        adGroupTargeting: '<',
        exclusionAdGroupTargeting: '<',
        audienceTargeting: '<',
        exclusionAudienceTargeting: '<',
        addTargeting: '&',
        removeTargeting: '&',
    },
    controllerAs: 'ctrl',
    controller: function (config) {
        var AD_GROUP_ENTITY = 'adGroup';
        var AUDIENCE_ENTITY = 'audience';
        var AD_GROUP_TARGETING = 'adGroupTargeting';
        var AUDIENCE_TARGETING = 'audienceTargeting';
        var EXCLUSION_AD_GROUP_TARGETING = 'exclusionAdGroupTargeting';
        var EXCLUSION_AUDIENCE_TARGETING = 'exclusionAudienceTargeting';

        var vm = this;
        vm.availableAudiencesAndAdGroups = [];
        vm.selectedTargeting = undefined;
        vm.selectedTargetings = [];
        vm.selectedExclusionTargetings = [];
        vm.config = config;

        vm.groupBySection = function (entity) {
            return entity.section;
        };

        vm.getAvailableAudiencesAndAdGroups = function () {
            var result = [];
            var i = 0;
            var audience = null;
            var adGroup = null;

            if (!vm.availableAudiences && !vm.availableAdGroups) {
                return result;
            }

            for (i = 0; i < vm.availableAudiences.length; i++) {
                audience = vm.availableAudiences[i];
                if (vm.audienceTargeting.indexOf(audience.id) < 0 &&
                        vm.exclusionAudienceTargeting.indexOf(audience.id) < 0 &&
                        !audience.archived) {
                    result.push(vm.getTargetingEntity(AUDIENCE_ENTITY, audience));
                }
            }

            for (i = 0; i < vm.availableAdGroups.length; i++) {
                adGroup = vm.availableAdGroups[i];
                if (vm.adGroupTargeting.indexOf(adGroup.id) < 0 &&
                        vm.exclusionAdGroupTargeting.indexOf(adGroup.id) < 0 &&
                        adGroup.id !== parseInt(vm.currentAdGroupId, 10) &&
                        !adGroup.archived) {
                    result.push(vm.getTargetingEntity(AD_GROUP_ENTITY, adGroup));
                }
            }

            return result;
        };

        vm.addSelectedTargeting = function (entity) {
            var type = AD_GROUP_TARGETING;
            if (entity.type === AUDIENCE_ENTITY) {
                type = AUDIENCE_TARGETING;
            }
            vm.addTargeting({type: type, id: entity.id});

            vm.selectedTargetings.push(entity);

            vm.selectedTargeting = undefined;

            vm.availableAudiencesAndAdGroups = vm.getAvailableAudiencesAndAdGroups();
        };

        vm.addSelectedExclusionTargeting = function (entity) {
            var type = EXCLUSION_AD_GROUP_TARGETING;
            if (entity.type === AUDIENCE_ENTITY) {
                type = EXCLUSION_AUDIENCE_TARGETING;
            }
            vm.addTargeting({type: type, id: entity.id});

            vm.selectedExclusionTargetings.push(entity);

            vm.selectedTargeting = undefined;

            vm.availableAudiencesAndAdGroups = vm.getAvailableAudiencesAndAdGroups();
        };

        vm.removeSelectedTargeting = function (entity) {
            var type = AD_GROUP_TARGETING;
            var i = 0;

            if (entity.type === AUDIENCE_ENTITY) {
                type = AUDIENCE_TARGETING;
            }

            vm.removeTargeting({type: type, id: entity.id});

            for (i = 0; i < vm.selectedTargetings.length; i++) {
                if (vm.selectedTargetings[i].id === entity.id && vm.selectedTargetings[i].type === entity.type) {
                    vm.selectedTargetings.splice(i, 1);
                    break;
                }
            }

            vm.availableAudiencesAndAdGroups = vm.getAvailableAudiencesAndAdGroups();
        };

        vm.removeSelectedExclusionTargeting = function (entity) {
            var type = EXCLUSION_AD_GROUP_TARGETING;
            var i = 0;

            if (entity.type === AUDIENCE_ENTITY) {
                type = EXCLUSION_AUDIENCE_TARGETING;
            }

            vm.removeTargeting({type: type, id: entity.id});

            for (i = 0; i < vm.selectedExclusionTargetings.length; i++) {
                if (vm.selectedExclusionTargetings[i].id === entity.id && vm.selectedExclusionTargetings[i].type === entity.type) {
                    vm.selectedExclusionTargetings.splice(i, 1);
                    break;
                }
            }

            vm.availableAudiencesAndAdGroups = vm.getAvailableAudiencesAndAdGroups();
        };

        vm.getTargetingEntity = function (type, entity) {
            if (type === AD_GROUP_ENTITY) {
                return {
                    type: AD_GROUP_ENTITY,
                    section: entity.campaignName,
                    id: entity.id,
                    name: entity.name,
                    archived: entity.archived
                };
            }

            return {
                type: AUDIENCE_ENTITY,
                section: 'Custom Audiences',
                id: entity.id,
                name: entity.name,
                archived: entity.archived
            };
        };

        vm.init = function () {
            var i = 0;
            var adGroup = null;
            var audience = null;

            for (i = 0; i < vm.availableAdGroups.length; i++) {
                adGroup = vm.availableAdGroups[i];
                if (vm.adGroupTargeting.indexOf(adGroup.id) >= 0) {
                    vm.selectedTargetings.push(vm.getTargetingEntity(AD_GROUP_ENTITY, adGroup));
                }

                if (vm.exclusionAdGroupTargeting.indexOf(adGroup.id) >= 0) {
                    vm.selectedExclusionTargetings.push(vm.getTargetingEntity(AD_GROUP_ENTITY, adGroup));
                }

            }

            for (i = 0; i < vm.availableAudiences.length; i++) {
                audience = vm.availableAudiences[i];
                if (vm.audienceTargeting.indexOf(audience.id) >= 0) {
                    vm.selectedTargetings.push(vm.getTargetingEntity(AUDIENCE_ENTITY, audience));
                }

                if (vm.exclusionAudienceTargeting.indexOf(audience.id) >= 0) {
                    vm.selectedExclusionTargetings.push(vm.getTargetingEntity(AUDIENCE_ENTITY, audience));
                }
            }

            vm.availableAudiencesAndAdGroups = vm.getAvailableAudiencesAndAdGroups();
        };

        vm.init();
    },
});
