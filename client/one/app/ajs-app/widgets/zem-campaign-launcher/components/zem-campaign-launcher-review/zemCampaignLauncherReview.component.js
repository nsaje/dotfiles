angular.module('one').component('zemCampaignLauncherReview', {
    bindings: {
        stateService: '=',
    },
    template: require('./zemCampaignLauncherReview.component.html'),
    controller: function () {
        var $ctrl = this;

        $ctrl.goToStep = $ctrl.stateService.goToStep;
        $ctrl.isGeoTargetingEnabled = isGeoTargetingEnabled;
        $ctrl.isDeviceTargetingEnabled = isDeviceTargetingEnabled;

        $ctrl.$onInit = function () {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.iabCategoryName = getIabCategoryName($ctrl.state.fields.iabCategory);
        };

        function getIabCategoryName (iabCategory) {
            for (var i = 0; i < options.iabCategories.length; i++) {
                if (options.iabCategories[i].value === iabCategory) {
                    return options.iabCategories[i].name;
                }
            }
        }

        function isGeoTargetingEnabled () {
            var enabled = false;
            Object.keys($ctrl.state.fields.targetRegions).forEach(function (key) {
                var section = $ctrl.state.fields.targetRegions[key] || [];
                if (section.length > 0) {
                    enabled = true;
                }
            });
            Object.keys($ctrl.state.fields.exclusionTargetRegions).forEach(function (key) {
                var section = $ctrl.state.fields.exclusionTargetRegions[key] || [];
                if (section.length > 0) {
                    enabled = true;
                }
            });
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
    },
});
