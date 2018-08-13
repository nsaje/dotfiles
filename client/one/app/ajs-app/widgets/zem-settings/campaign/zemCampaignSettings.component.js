angular.module('one.widgets').component('zemCampaignSettings', {
    bindings: {
        api: '<',
    },
    template: require('./zemCampaignSettings.component.html'),
    controller: function(zemPermissions) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.$onInit = function() {};
    },
});
