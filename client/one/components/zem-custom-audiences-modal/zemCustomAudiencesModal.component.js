/*globals angular,constants*/
'use strict';

angular.module('one.legacy').component('zemCustomAudiencesModal', {
    templateUrl: '/components/zem-custom-audiences-modal/zemCustomAudiencesModal.component.html',
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    controllerAs: 'ctrl',
    controller: ['api', function (api) {
        var vm = this;
        vm.accountId = vm.resolve.accountId;
        vm.audienceId = vm.resolve.audienceId;
        vm.readonly = vm.resolve.readonly;

        vm.listPixelsRequestInProgress = false;
        vm.putRequestInProgress = false;
        vm.getRequestInProgress = false;
        vm.pixels = [];
        vm.rules = [{id: 'visit', name: 'Anyone who visited your website'}, {id: 'referer', name: 'People who visited specific web pages'}];
        vm.refererRules = [{id: 'startsWith', name: 'URL equals'}, {id: 'contains', name: 'URL contains'}];
        vm.ttlDays = [{value: 7, name: '7'}, {value: 30, name: '30'}, {value: 90, name: '90'}, {value: 365, name: '365'}];

        vm.selectedTopRuleId = '';
        vm.selectedRefererRuleId = '';
        vm.selectedRefererRuleStartsWithValue = '';
        vm.selectedRefererRuleContainsValue = '';
        vm.selectedName = '';
        vm.selectedPixelId = null;
        vm.selectedTtl = null;

        vm.errors = {};

        vm.showRefererRules = function () {
            if (vm.selectedTopRuleId === 'referer') {
                return true;
            }
            return false;
        };

        vm.getPixels = function () {
            vm.listPixelsRequestInProgress = true;

            api.conversionPixel.list(vm.accountId).then(
                function (data) {
                    if (data.rows) {
                        vm.pixels = data.rows.filter(function (pixel) {
                            return !pixel.archived;
                        });
                    }
                },
                function (data) {
                    return;
                }
            ).finally(function () {
                vm.listPixelsRequestInProgress = false;
            });
        };

        vm.getAudience = function () {
            vm.getRequestInProgress = true;

            api.customAudiences.get(vm.accountId, vm.audienceId).then(
                function (data) {
                    if (data) {
                        vm.selectedName = data.name;
                        vm.selectedPixelId = data.pixelId;
                        vm.selectedTtl = data.ttl;
                        if (data.rules) {
                            var rule = data.rules[0];
                            if (rule.type === constants.audienceRuleType.VISIT) {
                                vm.selectedTopRuleId = 'visit';
                            } else if (rule.type === constants.audienceRuleType.STARTS_WITH) {
                                vm.selectedTopRuleId = 'referer';
                                vm.selectedRefererRuleId = 'startsWith';
                                vm.selectedRefererRuleStartsWithValue = rule.value;
                            } else if (rule.type === constants.audienceRuleType.CONTAINS) {
                                vm.selectedTopRuleId = 'referer';
                                vm.selectedRefererRuleId = 'contains';
                                if (rule.value && rule.value.length > 0) {
                                    vm.selectedRefererRuleContainsValue = rule.value.split(',').map(function (elem) {
                                        return {text: elem};
                                    });
                                }
                            }
                        }
                    }
                },
                function (data) {
                    // TODO: errors.
                    return;
                }
            ).finally(function () {
                vm.getRequestInProgress = false;
            });
        };

        vm.createAudience = function () {
            vm.putRequestInProgress = true;
            var i = 0;

            var audience = {
                name: vm.selectedName,
                pixel_id: vm.selectedPixelId,
                ttl: vm.selectedTtl,
            };
            var selectedRuleType = null;
            var selectedRuleValue = null;

            if (vm.selectedTopRuleId) {
                if (vm.selectedTopRuleId === 'visit') {
                    selectedRuleType = constants.audienceRuleType.VISIT;
                } else if (vm.selectedTopRuleId === 'referer') {
                    if (vm.selectedRefererRuleId === 'startsWith') {
                        selectedRuleType = constants.audienceRuleType.STARTS_WITH;
                        selectedRuleValue = vm.selectedRefererRuleStartsWithValue;
                    } else if (vm.selectedRefererRuleId === 'contains') {
                        selectedRuleType = constants.audienceRuleType.CONTAINS;
                        if (vm.selectedRefererRuleContainsValue && vm.selectedRefererRuleContainsValue.length > 0) {

                            selectedRuleValue = vm.selectedRefererRuleContainsValue.map(function (elem) {
                                return elem.text;
                            }).join(',');
                        }
                    }
                }
            }

            audience.rules = [{type: selectedRuleType, value: selectedRuleValue}];

            api.customAudiences.post(vm.accountId, audience).then(
                function (data) {
                    vm.modalInstance.close();
                },
                function (data) {
                    vm.errors = data;
                }
            ).finally(function () {
                vm.putRequestInProgress = false;
            });
        };

        function init () {
            vm.getPixels();
            if (vm.audienceId) {
                vm.getAudience(vm.audienceId);
            }
        }

        init();
    }],
});
