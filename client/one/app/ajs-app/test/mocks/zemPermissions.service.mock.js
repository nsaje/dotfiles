angular.module('one.mocks.zemPermissions', []).service('zemPermissions', function () {
    this.hasPermission = hasPermission;
    this.hasPermissionBCMv2 = hasPermission;
    this.isPermissionInternal = isPermissionInternal;
    this.isPermissionInternalBCMv2 = isPermissionInternal;
    this.setMockedPermissions = setMockedPermissions;
    this.setMockedInternalPermissions = setMockedInternalPermissions;

    var ALL_PERMISSIONS = 'allPermissions';
    this.ALL_PERMISSIONS = ALL_PERMISSIONS;

    var mockedPermissions = [];
    var internalPermissions = [];

    function hasPermission (permission) {
        if (mockedPermissions === ALL_PERMISSIONS) return true;
        if (!mockedPermissions.length) return false;

        var permissions;
        if (typeof permission === 'string') permissions = [permission];
        if (permission instanceof Array) permissions = permission;

        return permissions.every(function (p) {
            return mockedPermissions.indexOf(p) >= 0;
        });
    }

    function isPermissionInternal (permission) {
        if (internalPermissions === ALL_PERMISSIONS) return true;
        return internalPermissions.indexOf(permission) >= 0;
    }

    function setMockedPermissions (permissions) {
        mockedPermissions = permissions;
    }

    function setMockedInternalPermissions (permissions) {
        internalPermissions = permissions;
    }
});
