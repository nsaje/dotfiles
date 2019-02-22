angular.module('one.widgets').component('zemAccountSettings', {
    bindings: {
        api: '<',
    },
    template: require('./zemAccountSettings.component.html'),
    controller: function(zemPermissions) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.updatePublisherGroupsTargeting = updatePublisherGroupsTargeting;

        $ctrl.$onInit = function() {};

        function updatePublisherGroupsTargeting(entity, $event) {
            if ($event.whitelistedPublisherGroups) {
                entity.settings.whitelistPublisherGroups =
                    $event.whitelistedPublisherGroups;
            }
            if ($event.blacklistedPublisherGroups) {
                entity.settings.blacklistPublisherGroups =
                    $event.blacklistedPublisherGroups;
            }
        }
    },
});
