angular.module('one.widgets').service('zemAccessPermissionsDataService', function ($q, $http, zemUserService, zemAccessPermissionsEndpoint) { //eslint-disable-line max-len

    function PermissionsDataService (account) {
        var dataObject = {};

        // Public API
        this.getDataObject = getDataObject;
        this.initialize = initialize;
        this.create = create;
        this.remove = remove;
        this.activate = activate;
        this.undo = undo;
        this.promote = promote;
        this.downgrade = downgrade;

        function initialize () {
            zemUserService.list(account.id).then(
                function (data) {
                    dataObject.users = data.users;
                    dataObject.agencyManagers = data.agency_managers;
                    dataObject.users.forEach(function (user) {
                        user.action = null;
                        user.emailResent = false;
                    });
                }
            );
        }

        function getDataObject () {
            return dataObject;
        }

        function create (userData) {
            zemUserService.create(account.id, userData).then(
                function (data) {
                    var user = getUser(data.user.id);

                    if (!user) {
                        user = data.user;
                        dataObject.users.push(user);
                    } else {
                        user.name = data.user.name;
                    }

                    user.saved = true;
                    user.removed = false;
                    user.emailSent = data.created;
                    user.action = null;
                    dataObject.addUserErrors = null;
                    dataObject.addUserData = {};
                },
                function (data) {
                    dataObject.addUserErrors = data;
                }
            );
        }

        function remove (userId) {
            var user = getUser(userId);
            user.requestInProgress = true;

            zemUserService.remove(account.id, user.id).then(
                function () {
                    if (user) {
                        user.removed = true;
                        user.saved = false;
                    }
                }
            ).finally(function () {
                user.requestInProgress = false;
            });
        }

        function activate (userId) {
            var user = getUser(userId);
            user.requestInProgress = true;

            zemAccessPermissionsEndpoint.post(account.id, userId, 'activate').then(
                function () {
                    user.saved = true;
                    user.emailResent = true;
                },
                function () {
                    user.saved = false;
                    user.emailResent = false;
                }
            ).finally(function () {
                user.requestInProgress = false;
            });
        }

        function undo (userId) {
            var user = getUser(userId);
            user.requestInProgress = true;

            zemUserService.create(account.id, {email: user.email}).then(
                function () {
                    user.removed = false;
                }
            ).finally(function () {
                user.requestInProgress = false;
            });
        }

        function promote (userId) {
            var user = getUser(userId);
            user.requestInProgress = true;

            zemAccessPermissionsEndpoint.post(account.id, user.id, 'promote').then(
                function () {
                    user.is_agency_manager = true;
                }
            ).finally(function () {
                user.requestInProgress = false;
            });
        }

        function downgrade (user) {
            user.requestInProgress = true;

            zemAccessPermissionsEndpoint.post(account.id, user.id, 'downgrade').then(
                function () {
                    user.is_agency_manager = false;
                }
            ).finally(function () {
                user.requestInProgress = false;
            });
        }

        function getUser (userId) {
            return dataObject.users.filter(function (user) { return user.id === userId; })[0];
        }
    }

    return {
        getInstance: function (account) {
            return new PermissionsDataService(account);
        }
    };
});
