angular.module('one.widgets').component('zemCampaignSettings', {
    bindings: {
        entityId: '<',
    },
    templateUrl: '/app/widgets/zem-settings/campaign/zemCampaignSettings.component.html',
    controller: function (zemPermissions) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function () { };
    },
});
