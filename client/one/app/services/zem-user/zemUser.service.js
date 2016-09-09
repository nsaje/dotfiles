angular.module('one.services').service('zemUserService', ['zemUserEndpoint', function (zemUserEndpoint) {
    this.init = init;
    this.getUser = getUser;
    this.userHasPermissions = userHasPermissions;
    this.isPermissionInternal = isPermissionInternal;
    this.getUserId = getUserId;
    this.getUserEmail = getUserEmail;

    var user = null;

    function init () {
        return zemUserEndpoint.loadUser('current').then(function (_user_) {
            user = _user_;
        });
    }

    function getUser () {
        return user;
    }

    function userHasPermissions (permissions) {
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

    function getUserId () {
        return user ? user.id : null;
    }

    function getUserEmail () {
        return user ? user.email : null;
    }
}]);
