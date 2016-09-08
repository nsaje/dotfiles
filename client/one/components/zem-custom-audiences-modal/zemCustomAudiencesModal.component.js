/*globals angular,constants*/
'use strict';

angular.module('one.legacy').directive('zemCustomAudiencesModal', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        templateUrl: '/components/zem-custom-audiences-modal/zemCustomAudiencesModal.component.html',
        bindToController: {
            accountId: '=',
            closeModal: '=',
            successCallback: '&',
            audienceId: '=',
            readonly: '=',
        },
        controllerAs: 'ctrl',
        controller: 'ZemCustomAudiencesModalCtrl',
    };
}]);

angular.module('one.legacy').controller('ZemCustomAudiencesModalCtrl', ['api', function (api) {
    var vm = this;
    vm.listPixelsRequestInProgress = false;
    vm.putRequestInProgress = false;
    vm.getRequestInProgress = false;
    vm.pixels = [];
    vm.rules = [{id: 'visit', name: 'Anyone who visited your website'}, {id: 'referer', name: 'People who visited specific web pages'}];
    vm.refererRules = [{id: 'startsWith', name: 'URL equals'}, {id: 'contains', name: 'URL contains'}];
    vm.ttlDays = [{value: 7, name: '7'}, {value: 30, name: '30'}, {value: 90, name: '90'}];

    vm.selectedTopRuleId = '';
    vm.selectedRefererRuleId = '';
    vm.selectedRefererRuleValue = '';
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
                            vm.selectedRefererRuleValue = rule.value;
                        } else if (rule.type === constants.audienceRuleType.CONTAINS) {
                            vm.selectedTopRuleId = 'referer';
                            vm.selectedRefererRuleId = 'contains';
                            vm.selectedRefererRuleValue = rule.value;
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
                } else if (vm.selectedRefererRuleId === 'contains') {
                    selectedRuleType = constants.audienceRuleType.CONTAINS;
                }

                selectedRuleValue = vm.selectedRefererRuleValue;
            }
        }

        audience.rules = [{type: selectedRuleType, value: selectedRuleValue}];

        api.customAudiences.post(vm.accountId, audience).then(
            function (data) {
                // TODO: Call calback.
                vm.closeModal();
            },
            function (data) {
                vm.errors = data;
            }
        ).finally(function () {
            vm.putRequestInProgress = false;
        });
    };

    function init() {
        vm.getPixels();
        if (vm.audienceId) {
            vm.getAudience(vm.audienceId);
        }
    }

    init();
}]);
