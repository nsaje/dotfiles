/*globals angular,constants*/
'use strict';

angular.module('one.legacy').component('zemCustomAudiencesTargeting', {
    templateUrl: '/components/zem-custom-audiences-targeting/zemCustomAudiencesTargeting.component.html',
    bindings: {
        currentAdGroupId: '<',
        availableAdGroups: '<',
        availableAudiences: '<',
        adGroupTargeting: '=',
        audienceTargeting: '=',
        exclusionAudienceTargeting: '=',
    },
    controllerAs: 'ctrl',
    controller: ['config', function (config) {
        var vm = this;
        vm.selectedAdGroup = null;
        vm.selectedAudience = null;
        vm.selectedAdGroupTargeting = [];
        vm.selectedAudienceTargeting = [];
        vm.selectedExclusionAudienceTargeting = [];
        vm.config = config;

        vm.getAvailableAdGroups = function () {
            if (!vm.availableAdGroups) {
                return [];
            }

            var adgroups = vm.availableAdGroups.filter(function (adgroup) {
                return vm.adGroupTargeting.indexOf(adgroup.id) < 0;
            }).filter(function (adgroup) {
                return adgroup.id !== parseInt(vm.currentAdGroupId, 10);
            });

            adgroups.forEach(function (adgroup) {
                adgroup.suffix = '';
                if (adgroup.archived) {
                    adgroup.suffix = ' (Archived)';
                }
            });

            return adgroups;
        };

        vm.groupByCampaign = function (adgroup) {
            return adgroup.campaignName;
        };

        vm.getAvailableAudiences = function () {
            if (!vm.availableAudiences) {
                return [];
            }

            var audiences = vm.availableAudiences.filter(function (audience) {
                return vm.audienceTargeting.indexOf(audience.id) < 0 && vm.exclusionAudienceTargeting.indexOf(audience.id) < 0;
            });

            audiences.forEach(function (adgroup) {
                audiences.suffix = '';
                if (audiences.archived) {
                    audiences.suffix = ' (Archived)';
                }
            });

            return audiences;
        };

        vm.addAdgroup = function (adGroup) {
            vm.adGroupTargeting.push(adGroup.id);
            vm.selectedAdGroupTargeting.push({
                id: adGroup.id,
                name: adGroup.name
            });
            vm.selectedAdGroup = undefined;
        };

        vm.removeAdGroupTargeting = function (adGroup) {
            var selectedIdx = vm.adGroupTargeting.indexOf(adGroup.id);
            if (selectedIdx >= 0) {
                vm.adGroupTargeting.splice(selectedIdx, 1);
            }

            for (var i = 0; i < vm.selectedAdGroupTargeting.length; i++) {
                if (vm.selectedAdGroupTargeting[i].id === adGroup.id) {
                    vm.selectedAdGroupTargeting.splice(i, 1);
                    break;
                }
            }
        };

        vm.addAudienceTargeting = function (audience) {
            vm.audienceTargeting.push(audience.id);
            vm.selectedAudienceTargeting.push({
                id: audience.id,
                name: audience.name
            });
            vm.selectedAudience = undefined;
        };

        vm.removeAudienceTargeting = function (audience) {
            var selectedIdx = vm.audienceTargeting.indexOf(audience.id);
            if (selectedIdx >= 0) {
                vm.audienceTargeting.splice(selectedIdx, 1);
            }

            for (var i = 0; i < vm.selectedAudienceTargeting.length; i++) {
                if (vm.selectedAudienceTargeting[i].id === audience.id) {
                    vm.selectedAudienceTargeting.splice(i, 1);
                    break;
                }
            }
        };

        vm.addExclusionAudienceTargeting = function (audience) {
            vm.exclusionAudienceTargeting.push(audience.id);
            vm.selectedExclusionAudienceTargeting.push({
                id: audience.id,
                name: audience.name
            });
            vm.selectedAudience = undefined;
        };

        vm.removeExclusionAudienceTargeting = function (audience) {
            var selectedIdx = vm.exclusionAudienceTargeting.indexOf(audience.id);
            if (selectedIdx >= 0) {
                vm.exclusionAudienceTargeting.splice(selectedIdx, 1);
            }

            for (var i = 0; i < vm.selectedExclusionAudienceTargeting.length; i++) {
                if (vm.selectedExclusionAudienceTargeting[i].id === audience.id) {
                    vm.selectedExclusionAudienceTargeting.splice(i, 1);
                    break;
                }
            }
        };

        vm.init = function () {
            vm.selectedAdGroupTargeting = vm.availableAdGroups.filter(function (adGroup) {
                return vm.adGroupTargeting.indexOf(adGroup.id) >= 0;
            });
            vm.selectedAudienceTargeting = vm.availableAudiences.filter(function (audience) {
                return vm.audienceTargeting.indexOf(audience.id) >= 0;
            });
            vm.selectedExclusionAudienceTargeting = vm.availableAudiences.filter(function (audience) {
                return vm.exclusionAudienceTargeting.indexOf(audience.id) >= 0;
            });
        };

        vm.init();
    }],
});
