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
            if ($ctrl.state.fields.targetRegions && $ctrl.state.fields.targetRegions.length) {
                return true;
            }
            if ($ctrl.state.fields.exclusionTargetRegions && $ctrl.state.fields.exclusionTargetRegions.length) {
                return true;
            }
            return false;
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
