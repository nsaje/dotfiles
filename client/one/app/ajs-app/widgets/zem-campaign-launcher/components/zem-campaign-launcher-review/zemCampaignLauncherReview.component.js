require('./zemCampaignLauncherReview.component.less');
var constantsHelpers = require('../../../../../shared/helpers/constants.helpers');
var currencyHelpers = require('../../../../../shared/helpers/currency.helpers');
var iframeHelpers = require('../../../../../shared/helpers/iframe.helpers');

angular.module('one').component('zemCampaignLauncherReview', {
    bindings: {
        stateService: '=',
        account: '<',
    },
    template: require('./zemCampaignLauncherReview.component.html'),
    controller: function(zemDeviceTargetingConstants, zemPermissions, $filter) {
        var $ctrl = this;

        $ctrl.hasPermission = zemPermissions.hasPermission;

        var PREVIEW_CREATIVES_PER_ROW = 4;

        $ctrl.goToStep = $ctrl.stateService.goToStep;
        $ctrl.isGeoTargetingEnabled = isGeoTargetingEnabled;
        $ctrl.isDeviceTargetingEnabled = isDeviceTargetingEnabled;
        $ctrl.adType = constants.adType;

        $ctrl.$onInit = function() {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.iabCategoryName = getIabCategoryName(
                $ctrl.state.fields.iabCategory
            );
            $ctrl.language = getLanguageName($ctrl.state.fields.language);
            $ctrl.currencySymbol = currencyHelpers.getCurrencySymbol(
                $ctrl.account.currency
            );
            $ctrl.campaignGoalText = $filter('campaignGoalText')(
                $ctrl.state.fields.campaignGoal
            );
            $ctrl.dummyCreatives = getDummyCreatives(
                $ctrl.state.creatives.candidates || []
            );

            var campaignType = parseInt(
                constantsHelpers.convertFromName(
                    $ctrl.state.fields.type,
                    constants.campaignTypes
                )
            );
            $ctrl.isDisplayCampaign =
                campaignType === constants.campaignTypes.DISPLAY;

            updateDeviceTargetingReview();
        };

        $ctrl.renderAdTagInIframe = function(adTag) {
            var iframe = document.getElementById('creative__iframe');
            iframeHelpers.renderContentInIframe(iframe, adTag);
        };

        function getIabCategoryName(iabCategory) {
            for (var i = 0; i < options.iabCategories.length; i++) {
                if (options.iabCategories[i].value === iabCategory) {
                    return options.iabCategories[i].name;
                }
            }
        }

        function getLanguageName(language) {
            var languages = constantsHelpers.convertToRestApiCompliantOptions(
                options.languages,
                constants.language
            );
            for (var i = 0; i < languages.length; i++) {
                if (languages[i].value === language) {
                    return languages[i].name;
                }
            }
        }

        function getDummyCreatives(candidates) {
            // Return an array of length equal to number of dummy creatives needed (used by ng-repeat in template to
            // fill in dummy creatives).
            var m = candidates.length % PREVIEW_CREATIVES_PER_ROW;
            if (m !== 0) {
                return new Array(PREVIEW_CREATIVES_PER_ROW - m);
            }
            return [];
        }

        function isGeoTargetingEnabled() {
            var enabled = false;
            if ($ctrl.state.fields.targetRegions) {
                Object.keys($ctrl.state.fields.targetRegions).forEach(function(
                    key
                ) {
                    var section = $ctrl.state.fields.targetRegions[key] || [];
                    if (section.length > 0) {
                        enabled = true;
                    }
                });
            }
            if ($ctrl.state.fields.exclusionTargetRegions) {
                Object.keys($ctrl.state.fields.exclusionTargetRegions).forEach(
                    function(key) {
                        var section =
                            $ctrl.state.fields.exclusionTargetRegions[key] ||
                            [];
                        if (section.length > 0) {
                            enabled = true;
                        }
                    }
                );
            }
            return enabled;
        }

        function isDeviceTargetingEnabled() {
            if (
                $ctrl.state.fields.targetDevices &&
                $ctrl.state.fields.targetDevices.length
            ) {
                return true;
            }
            if (
                $ctrl.state.fields.targetOs &&
                $ctrl.state.fields.targetOs.length
            ) {
                return true;
            }
            if (
                $ctrl.state.fields.targetPlacements &&
                $ctrl.state.fields.targetPlacements.length
            ) {
                return true;
            }
            return false;
        }

        function updateDeviceTargetingReview() {
            $ctrl.targetedDevices = null;

            if (!$ctrl.state || !$ctrl.state.fields) {
                return;
            }

            if (
                $ctrl.state.fields.targetDevices &&
                $ctrl.state.fields.targetDevices.length
            ) {
                var targetedDevices = [];
                zemDeviceTargetingConstants.DEVICES.forEach(function(device) {
                    if (
                        $ctrl.state.fields.targetDevices.indexOf(
                            device.value
                        ) !== -1
                    ) {
                        targetedDevices.push(device.name);
                    }
                });
                $ctrl.targetedDevices = targetedDevices.join(', ');
            }
        }
    },
});
