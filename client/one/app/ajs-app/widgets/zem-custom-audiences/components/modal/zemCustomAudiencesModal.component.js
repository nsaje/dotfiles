angular.module('one.widgets').component('zemCustomAudiencesModal', {
    template: require('./zemCustomAudiencesModal.component.html'),
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    controller: function() {
        var $ctrl = this;

        $ctrl.rules = [
            {id: 'visit', name: 'Anyone who visited your website'},
            {id: 'referer', name: 'People who visited specific web pages'},
        ];
        $ctrl.refererRules = [
            {id: 'contains', name: 'URL contains'},
            {id: 'startsWith', name: 'URL equals'},
        ];
        $ctrl.currentAudiencePixel = null;
        $ctrl.pixels = [];
        $ctrl.selectedPixel = null;
        $ctrl.selectedTopRuleId = '';
        $ctrl.selectedRefererRuleId = '';
        $ctrl.selectedRefererRuleStartsWithValue = '';
        $ctrl.selectedRefererRuleContainsValue = '';
        $ctrl.selectedName = '';
        $ctrl.selectedTtl = 90;
        $ctrl.title = '';

        $ctrl.updateAudience = updateAudience;
        $ctrl.createAudience = createAudience;
        $ctrl.showRefererRules = showRefererRules;
        $ctrl.getRequest = getRequest;
        $ctrl.clearValidationError = clearValidationError;
        $ctrl.loadPixels = loadPixels;

        $ctrl.$onInit = function() {
            $ctrl.isCreationMode = !$ctrl.resolve.audience;

            $ctrl.audience = $ctrl.resolve.audience;
            $ctrl.stateService = $ctrl.resolve.stateService;
            $ctrl.state = $ctrl.stateService.getState();

            if ($ctrl.isCreationMode) {
                $ctrl.title = 'Create Custom Audience';
                loadPixels();
            } else {
                $ctrl.title = 'Edit Custom Audience';
                loadAudience();
            }
        };

        $ctrl.$onDestroy = function() {
            // Clean-up request errors if any
            var request = getRequest();
            if (request && request.validationErrors) {
                delete request.validationErrors;
            }
        };

        function loadAudience() {
            $ctrl.stateService.get($ctrl.audience.id).then(function(audience) {
                loadPixels().then(function() {
                    loadAudienceData(audience);
                });
            });
        }

        function createAudience() {
            var request = getRequest();
            if (request && request.inProgress) {
                return;
            }

            var audienceData = createAudienceData();
            $ctrl.stateService.create(audienceData).then(function() {
                $ctrl.modalInstance.close();
            });
        }

        function updateAudience() {
            var request = getRequest();
            if (request && request.inProgress) {
                return;
            }

            var data = {name: $ctrl.selectedName};
            data.pixel_id = $ctrl.selectedPixel
                ? $ctrl.selectedPixel.id
                : $ctrl.currentAudiencePixel.id;
            $ctrl.stateService.update($ctrl.audience.id, data).then(function() {
                $ctrl.modalInstance.close();
            });
        }

        function loadAudienceData(audience) {
            $ctrl.selectedName = audience.name;
            $ctrl.selectedTtl = audience.ttl;
            $ctrl.currentAudiencePixel = $ctrl.pixels.find(function(pi) {
                return pi.id === parseInt(audience.pixelId);
            });
            if (audience.rules) {
                var rule = audience.rules[0];
                if (rule.type === constants.audienceRuleType.VISIT) {
                    $ctrl.selectedTopRuleId = 'visit';
                } else if (
                    rule.type === constants.audienceRuleType.STARTS_WITH
                ) {
                    $ctrl.selectedTopRuleId = 'referer';
                    $ctrl.selectedRefererRuleId = 'startsWith';
                    if (rule.value && rule.value.length > 0) {
                        $ctrl.selectedRefererRuleStartsWithValue = getTagsFromText(
                            rule.value
                        );
                    }
                } else if (rule.type === constants.audienceRuleType.CONTAINS) {
                    $ctrl.selectedTopRuleId = 'referer';
                    $ctrl.selectedRefererRuleId = 'contains';
                    if (rule.value && rule.value.length > 0) {
                        $ctrl.selectedRefererRuleContainsValue = getTagsFromText(
                            rule.value
                        );
                    }
                }
            }
        }

        function createAudienceData() {
            var audience = {
                name: $ctrl.selectedName,
                pixel_id: $ctrl.selectedPixel.id,
                ttl: $ctrl.selectedTtl,
            };
            var selectedRuleType = null;
            var selectedRuleValue = null;

            if ($ctrl.selectedTopRuleId) {
                if ($ctrl.selectedTopRuleId === 'visit') {
                    selectedRuleType = constants.audienceRuleType.VISIT;
                } else if ($ctrl.selectedTopRuleId === 'referer') {
                    if ($ctrl.selectedRefererRuleId === 'startsWith') {
                        selectedRuleType =
                            constants.audienceRuleType.STARTS_WITH;
                        if (
                            $ctrl.selectedRefererRuleStartsWithValue &&
                            $ctrl.selectedRefererRuleStartsWithValue.length > 0
                        ) {
                            selectedRuleValue = getTextFromTags(
                                $ctrl.selectedRefererRuleStartsWithValue
                            );
                        }
                    } else if ($ctrl.selectedRefererRuleId === 'contains') {
                        selectedRuleType = constants.audienceRuleType.CONTAINS;
                        if (
                            $ctrl.selectedRefererRuleContainsValue &&
                            $ctrl.selectedRefererRuleContainsValue.length > 0
                        ) {
                            selectedRuleValue = getTextFromTags(
                                $ctrl.selectedRefererRuleContainsValue
                            );
                        }
                    }
                }
            }

            audience.rules = [
                {type: selectedRuleType, value: selectedRuleValue},
            ];
            return audience;
        }

        function loadPixels() {
            return $ctrl.stateService.listAudiencePixels().then(function() {
                $ctrl.pixels = $ctrl.state.audiencePixels.filter(function(pi) {
                    return !pi.archived;
                });
            });
        }

        function getRequest() {
            if ($ctrl.isCreationMode) {
                return $ctrl.state.requests.create;
            }
            return $ctrl.state.requests.update[$ctrl.audience.id];
        }

        function clearValidationError(field) {
            $ctrl.stateService.clearRequestError(getRequest(), field);
        }

        function getTextFromTags(tags) {
            return tags
                .map(function(elem) {
                    return elem.text;
                })
                .join(',');
        }

        function getTagsFromText(text) {
            return text.split(',').map(function(elem) {
                return {text: elem};
            });
        }

        function showRefererRules() {
            return $ctrl.selectedTopRuleId === 'referer';
        }
    },
});
