angular.module('one.services').service('zemPermissions', function (zemUserService) {
    var NOT_PUBLIC_ANYMORE = [
        'zemauth.can_view_platform_cost_breakdown_derived',
        'zemauth.can_view_platform_cost_breakdown',
        'zemauth.can_view_agency_margin',
        'zemauth.can_view_flat_fees',
    ];

    this.hasPermission = hasPermission;
    this.hasPermissionBCMv2 = hasPermissionBCMv2;
    this.isPermissionInternal = isPermissionInternal;
    this.isPermissionInternalBCMv2 = isPermissionInternalBCMv2;
    this.canAccessPlatformCosts = canAccessPlatformCosts;
    this.canAccessAgencyCosts = canAccessAgencyCosts;

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

        return permissions.every(function (permission) {
            return Object.keys(user.permissions).indexOf(permission) >= 0;
        });
    }

    function hasPermissionBCMv2 (permission, usesBCMv2) {
        var permissions;
        if (typeof permission === 'string') permissions = [permission];
        if (permission instanceof Array) permissions = permission;

        var user = zemUserService.current();
        if (!user || !permissions) {
            return false;
        }

        return permissions.every(function (permission) {
            // special exception for this permission
            if (!usesBCMv2 && NOT_PUBLIC_ANYMORE.indexOf(permission) >= 0) {
                return true;
            }
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

    function isPermissionInternalBCMv2 (permission, usesBCMv2) {
        var user = zemUserService.current();
        if (!user || Object.keys(user.permissions).indexOf(permission) < 0) {
            return false;
        }

        if (!usesBCMv2 && NOT_PUBLIC_ANYMORE.indexOf(permission) >= 0) {
            return false;
        }

        return !user.permissions[permission];
    }

    function canAccessPlatformCosts (activeAccount) {
        return activeAccount &&
            (!activeAccount.data.usesBCMv2 || hasPermission('zemauth.can_view_platform_cost_breakdown'));
    }

    function canAccessAgencyCosts (activeAccount) {
        return activeAccount && (
            (activeAccount.data.usesBCMv2 &&
             hasPermission('zemauth.can_view_agency_cost_breakdown')) ||
                (!activeAccount.data.usesBCMv2 &&
                 hasPermission('zemauth.can_manage_agency_margin')));
    }
});
