angular.module('one').component('zemCampaignLauncherGeneralSettings', {
    bindings: {
        stateService: '<',
    },
    templateUrl: '/app/widgets/zem-campaign-launcher/components/zem-campaign-launcher-general-settings/zemCampaignLauncherGeneralSettings.component.html', // eslint-disable-line max-len
    controller: function () {
        var $ctrl = this;

        $ctrl.onFieldChange = onFieldChange;

        $ctrl.$onInit = function () {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.availableIabCategories = options.iabCategories.slice().sort(function (obj1, obj2) {
                if (obj1.value === constants.iabCategory.IAB24) {
                    return -1;
                }
                if (obj2.value === constants.iabCategory.IAB24) {
                    return 1;
                }
                return obj1.name.localeCompare(obj2.name);
            });
        };

        function onFieldChange () {
            $ctrl.stateService.validateFields();
        }
    },
});
