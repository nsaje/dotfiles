angular.module('one.widgets').component('zemCampaignGeneralSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/campaign/general/zemCampaignGeneralSettings.component.html',
    controller: function (zemPermissions) {
        var $ctrl = this,
            iabCategoriesSorted = options.legacyIabCategories.slice();
        iabCategoriesSorted.sort(sortIab);

        $ctrl.iabCategoriesSorted = iabCategoriesSorted;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };

        function sortIab (obj1, obj2) {
            if (obj1.value === constants.legacyIabCategory.IAB24) {
                return -1;
            }
            if (obj2.value === constants.legacyIabCategory.IAB24) {
                return 1;
            }
            return obj1.name.localeCompare(obj2.name);
        }
    },
});
