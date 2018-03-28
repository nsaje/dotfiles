require('./zemCampaignLauncherReview.component.less');

angular.module('one').component('zemCampaignLauncherReview', {
    bindings: {
        stateService: '=',
    },
    template: require('./zemCampaignLauncherReview.component.html'),
    controller: function (zemDeviceTargetingConstants, zemPermissions, $filter) {
        var $ctrl = this;

        $ctrl.hasPermission = zemPermissions.hasPermission;

        var PREVIEW_CREATIVES_PER_ROW = 4;

        $ctrl.goToStep = $ctrl.stateService.goToStep;
        $ctrl.isGeoTargetingEnabled = isGeoTargetingEnabled;
        $ctrl.isDeviceTargetingEnabled = isDeviceTargetingEnabled;

        $ctrl.$onInit = function () {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.iabCategoryName = getIabCategoryName($ctrl.state.fields.iabCategory);
            $ctrl.language = getLanguageName($ctrl.state.fields.language);
            // TODO (jurebajt): Set unit dynamically when multi-currency support is added to campaign launcher
            $ctrl.campaignGoalText = $filter('campaignGoalText')($ctrl.state.fields.campaignGoal);
            // HACK (jurebajt): Replace euro currency sign with dollar sign. Remove when multi-currency support is added
            // to campaign launcher!
            $ctrl.campaignGoalText = $ctrl.campaignGoalText.replace('€', '$');
            $ctrl.dummyCreatives = getDummyCreatives($ctrl.state.creatives.candidates || []);

            updateDeviceTargetingReview();
        };

        function getIabCategoryName (iabCategory) {
            for (var i = 0; i < options.iabCategories.length; i++) {
                if (options.iabCategories[i].value === iabCategory) {
                    return options.iabCategories[i].name;
                }
            }
        }

        function getLanguageName (language) {
            for (var i = 0; i < options.languages.length; i++) {
                if (options.languages[i].value === language) {
                    return options.languages[i].name;
                }
            }
        }

        function getDummyCreatives (candidates) {
            // Return an array of length equal to number of dummy creatives needed (used by ng-repeat in template to
            // fill in dummy creatives).
            var m = candidates.length % PREVIEW_CREATIVES_PER_ROW;
            if (m !== 0) {
                return new Array(PREVIEW_CREATIVES_PER_ROW - m);
            }
            return [];
        }

        function isGeoTargetingEnabled () {
            var enabled = false;
            if ($ctrl.state.fields.targetRegions) {
                Object.keys($ctrl.state.fields.targetRegions).forEach(function (key) {
                    var section = $ctrl.state.fields.targetRegions[key] || [];
                    if (section.length > 0) {
                        enabled = true;
                    }
                });
            }
            if ($ctrl.state.fields.exclusionTargetRegions) {
                Object.keys($ctrl.state.fields.exclusionTargetRegions).forEach(function (key) {
                    var section = $ctrl.state.fields.exclusionTargetRegions[key] || [];
                    if (section.length > 0) {
                        enabled = true;
                    }
                });
            }
            return enabled;
        }

        function isDeviceTargetingEnabled () {
            if ($ctrl.state.fields.targetDevices && $ctrl.state.fields.targetDevices.length) {
                return true;
            }
            if ($ctrl.state.fields.targetOs && $ctrl.state.fields.targetOs.length) {
                return true;
            }
            if ($ctrl.state.fields.targetPlacements && $ctrl.state.fields.targetPlacements.length) {
                return true;
            }
            return false;
        }

        function updateDeviceTargetingReview () {
            $ctrl.targetedDevices = null;

            if (!$ctrl.state || !$ctrl.state.fields) {
                return;
            }

            if ($ctrl.state.fields.targetDevices && $ctrl.state.fields.targetDevices.length) {
                var targetedDevices = [];
                zemDeviceTargetingConstants.DEVICES.forEach(function (device) {
                    if ($ctrl.state.fields.targetDevices.indexOf(device.value) !== -1) {
                        targetedDevices.push(device.name);
                    }
                });
                $ctrl.targetedDevices = targetedDevices.join(', ');
            }
        }
    },
});
