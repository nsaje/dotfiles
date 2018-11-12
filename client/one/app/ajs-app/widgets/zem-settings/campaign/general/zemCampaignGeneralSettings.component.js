angular.module('one.widgets').component('zemCampaignGeneralSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemCampaignGeneralSettings.component.html'),
    controller: function(zemPermissions) {
        var $ctrl = this,
            iabCategoriesSorted = options.legacyIabCategories.slice();
        iabCategoriesSorted.sort(sortIab);

        $ctrl.iabCategoriesSorted = iabCategoriesSorted;
        $ctrl.languages = options.languages;
        $ctrl.campaignTypes = options.campaignTypes.filter(filterTypes);
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function() {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };

        $ctrl.$onChanges = function() {
            if (
                $ctrl.entity &&
                !zemPermissions.hasPermission(
                    'zemauth.can_see_campaign_language_choices'
                ) &&
                !$ctrl.entity.settings.language
            ) {
                $ctrl.entity.settings.language = constants.language.ENGLISH;
            }
            if (
                $ctrl.entity &&
                !zemPermissions.hasPermission(
                    'zemauth.fea_can_change_campaign_type'
                ) &&
                !$ctrl.entity.settings.type
            ) {
                $ctrl.entity.settings.type = constants.campaignTypes.CONTENT;
            }
        };

        function sortIab(obj1, obj2) {
            if (obj1.value === constants.legacyIabCategory.IAB24) {
                return -1;
            }
            if (obj2.value === constants.legacyIabCategory.IAB24) {
                return 1;
            }
            return obj1.name.localeCompare(obj2.name);
        }

        function filterTypes(option) {
            if (
                option.value === constants.campaignTypes.DISPLAY &&
                !zemPermissions.hasPermission(
                    'zemauth.fea_can_change_campaign_type_to_display'
                )
            ) {
                return false;
            }
            return true;
        }
    },
});
