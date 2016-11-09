angular.module('one.widgets').component('zemCampaignGeneralSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/campaign/general/zemCampaignGeneralSettings.component.html',
    controller: ['zemPermissions', function (zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };
    }],
});
