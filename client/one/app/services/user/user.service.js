angular.module('one.services').service('userService', [function () {
    this.init = init;
    this.hasPermission = hasPermission;
    this.isPermissionInternal = isPermissionInternal;
    this.getEmail = getEmail;

    var user = null;

    function init (currentUser) {
        user = currentUser;
    }

    function hasPermission (permissions) {
        if (!user || !permissions) {
            return false;
        }

        // Can take string or array, returns true if user has any of the permissions
        if (typeof permissions === 'string') {
            permissions = [permissions];
        }

        return permissions.some(function (permission) {
            return Object.keys(user.permissions).indexOf(permission) >= 0;
        });
    }

    function isPermissionInternal (permission) {
        if (!user || Object.keys(user.permissions).indexOf(permission) < 0) {
            return false;
        }

        return !user.permissions[permission];
    }

    function getEmail () {
        return user ? user.email : null;
    }
}]);
