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

        vm.postRequestInProgress = false;
        vm.putRequestInProgress = false;
        vm.getRequestInProgress = false;
        vm.pixel = null;
        vm.rules = [{id: 'visit', name: 'Anyone who visited your website'}, {id: 'referer', name: 'People who visited specific web pages'}];
        vm.refererRules = [{id: 'contains', name: 'URL contains'}, {id: 'startsWith', name: 'URL equals'}];
        vm.ttlDays = [{value: 7, name: '7'}, {value: 30, name: '30'}, {value: 90, name: '90'}, {value: 365, name: '365'}];

        vm.selectedTopRuleId = '';
        vm.selectedRefererRuleId = '';
        vm.selectedRefererRuleStartsWithValue = '';
        vm.selectedRefererRuleContainsValue = '';
        vm.selectedName = '';
        vm.selectedTtl = null;

        vm.errors = {};

        function getTextFromTags (tags) {
            var result = tags.map(function (elem) {
                return elem.text;
            }).join(',');

            return result;
        }

        function getTagsFromText (text) {
            var result = text.split(',').map(function (elem) {
                return {text: elem};
            });

            return result;
        }

        vm.showRefererRules = function () {
            if (vm.selectedTopRuleId === 'referer') {
                return true;
            }
            return false;
        };

        vm.getPixel = function (pixelId, audienceOnly) {
            api.conversionPixel.list(vm.accountId, audienceOnly).then(
                function (data) {
                    if (data.rows) {
                        var audiencePixels = data.rows.filter(function (pixel) {
                            if (pixelId) {
                                return pixel.id.toString() === pixelId;
                            }

                            return pixel.audienceEnabled;
                        });


                        if (audiencePixels.length > 0) {
                            audiencePixels[0].id = audiencePixels[0].id.toString();
                            vm.pixel = audiencePixels[0];
                        }
                    }
                },
                function (data) {
                    return;
                }
            );
        };

        vm.getAudience = function () {
            vm.getRequestInProgress = true;

            api.customAudiences.get(vm.accountId, vm.audienceId).then(
                function (data) {
                    if (data) {
                        vm.selectedName = data.name;
                        vm.selectedTtl = data.ttl;
                        if (data.rules) {
                            var rule = data.rules[0];
                            if (rule.type === constants.audienceRuleType.VISIT) {
                                vm.selectedTopRuleId = 'visit';
                            } else if (rule.type === constants.audienceRuleType.STARTS_WITH) {
                                vm.selectedTopRuleId = 'referer';
                                vm.selectedRefererRuleId = 'startsWith';
                                if (rule.value && rule.value.length > 0) {
                                    vm.selectedRefererRuleStartsWithValue = getTagsFromText(rule.value);
                                }
                            } else if (rule.type === constants.audienceRuleType.CONTAINS) {
                                vm.selectedTopRuleId = 'referer';
                                vm.selectedRefererRuleId = 'contains';
                                if (rule.value && rule.value.length > 0) {
                                    vm.selectedRefererRuleContainsValue = getTagsFromText(rule.value);
                                }
                            }
                        }

                        vm.getPixel(data.pixelId);
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
            if (vm.postRequestInProgress) {
                return;
            }

            vm.postRequestInProgress = true;

            var audience = {
                name: vm.selectedName,
                pixel_id: vm.pixel.id,
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
                        if (vm.selectedRefererRuleStartsWithValue && vm.selectedRefererRuleStartsWithValue.length > 0) {

                            selectedRuleValue = getTextFromTags(vm.selectedRefererRuleStartsWithValue);
                        }
                    } else if (vm.selectedRefererRuleId === 'contains') {
                        selectedRuleType = constants.audienceRuleType.CONTAINS;
                        if (vm.selectedRefererRuleContainsValue && vm.selectedRefererRuleContainsValue.length > 0) {

                            selectedRuleValue = getTextFromTags(vm.selectedRefererRuleContainsValue);
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
                    vm.postRequestInProgress = false;
                }
            );
        };

        vm.updateAudience = function () {
            if (vm.putRequestInProgress) {
                return;
            }

            vm.putRequestInProgress = true;

            var audience = {name: vm.selectedName};

            api.customAudiences.put(vm.accountId, vm.audienceId, audience).then(
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

        vm.removeError = function (field) {
            if (vm.errors) {
                delete vm.errors[field];
            }
        };

        function init () {
            if (vm.audienceId) {
                vm.getAudience(vm.audienceId);
            } else {
                vm.getPixel();
            }
        }

        init();
    }],
});
