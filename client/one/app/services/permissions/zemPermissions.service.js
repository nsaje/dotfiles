angular.module('one.services').service('zemPermissions', function (zemUserService) {
    this.hasPermission = hasPermission;
    this.isPermissionInternal = isPermissionInternal;

    function hasPermission (permission) {
        // Can take string or array (legacy option), returns true if user has any of the permissions
        // TODO: remove option to pass array
        var permissions;
        if (typeof permission === 'string') permissions = [permission];
        if (permission instanceof Array) permissions = permission;

        var user = zemUserService.current();
        if (!user || !permissions) {
            return false;
        }

        return permissions.some(function (permission) {
            return Object.keys(user.permissions).indexOf(permission) >= 0;
        });
    }

    function isPermissionInternal (permission) {
        var user = zemUserService.current();
        if (!user || Object.keys(user.permissions).indexOf(permission) < 0) {
            return false;
        }

        return !user.permissions[permission];
    }
});
