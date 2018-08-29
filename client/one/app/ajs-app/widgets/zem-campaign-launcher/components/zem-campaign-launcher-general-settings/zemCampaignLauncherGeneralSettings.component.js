require('./zemCampaignLauncherGeneralSettings.component.less');
var constantsHelpers = require('../../../../../shared/helpers/constants.helpers');

angular.module('one').component('zemCampaignLauncherGeneralSettings', {
    bindings: {
        stateService: '<',
        account: '<',
    },
    template: require('./zemCampaignLauncherGeneralSettings.component.html'),
    controller: function(zemPermissions, zemMulticurrencyService) {
        var $ctrl = this;

        $ctrl.onFieldChange = onFieldChange;
        $ctrl.hasPermission = zemPermissions.hasPermission;

        $ctrl.$onInit = function() {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.availableIabCategories = getAvailableIabCategories();
            $ctrl.availableLanguages = constantsHelpers.convertToRestApiCompliantOptions(
                options.languages,
                constants.language
            );
            if (
                !zemPermissions.hasPermission(
                    'zemauth.can_see_campaign_language_choices'
                )
            ) {
                $ctrl.state.fields.language = constantsHelpers.convertToName(
                    constants.language.ENGLISH,
                    constants.language
                );
            }
            $ctrl.currencySymbol = zemMulticurrencyService.getAppropriateCurrencySymbol(
                $ctrl.account
            );
        };

        function onFieldChange() {
            $ctrl.stateService.validateFields();
        }

        function getAvailableIabCategories() {
            function iabSort(obj1, obj2) {
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
