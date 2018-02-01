require('./zemCampaignLauncherGeneralSettings.component.less');

angular.module('one').component('zemCampaignLauncherGeneralSettings', {
    bindings: {
        stateService: '<',
        account: '<',
    },
    template: require('./zemCampaignLauncherGeneralSettings.component.html'), // eslint-disable-line max-len
    controller: function (zemPermissions) {
        var $ctrl = this;

        $ctrl.onFieldChange = onFieldChange;
        $ctrl.hasPermission = zemPermissions.hasPermission;

        $ctrl.$onInit = function () {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.availableIabCategories = getAvailableIabCategories();
            $ctrl.availableLanguages = options.languages;
            if (!zemPermissions.hasPermission('zemauth.can_see_campaign_language_choices')) {
                $ctrl.state.fields.language = 'ENGLISH';
            }
        };

        function onFieldChange () {
            $ctrl.stateService.validateFields();
        }

        function getAvailableIabCategories () {
            function iabSort (obj1, obj2) {
                if (obj1.value === constants.iabCategory.IAB24) {
                    return -1;
                }
                if (obj2.value === constants.iabCategory.IAB24) {
                    return 1;
                }
                return obj1.name.localeCompare(obj2.name);
            }

            return options.iabCategories.slice().sort(iabSort);
        }
    },
});
