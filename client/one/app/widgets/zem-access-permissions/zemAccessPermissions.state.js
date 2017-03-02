angular.module('one.widgets').service('zemAccessPermissionsStateService', function ($q, $http, zemUserService, zemAccessPermissionsEndpoint) { //eslint-disable-line max-len

    function StateService (account) {
        var state = {};

        // Public API
        this.getState = getState;
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
                    state.users = data.users;
                    state.agencyManagers = data.agency_managers;
                    state.users.forEach(function (user) {
                        user.action = null;
                        user.emailResent = false;
                    });
                }
            );
        }

        function getState () {
            return state;
        }

        function create (userData) {
            return zemUserService.create(account.id, userData).then(
                function (data) {
                    var user = getUser(data.user.id);

                    if (!user) {
                        user = data.user;
                        state.users.push(user);
                    } else {
                        user.name = data.user.name;
                    }

                    user.saved = true;
                    user.removed = false;
                    user.emailSent = data.created;
                    user.action = null;
                    state.addUserErrors = null;
                    state.addUserData = {};
                },
                function (data) {
                    state.addUserErrors = data;
                    return $q.reject(data);
                }
            );
        }

        function remove (user) {
            user.requestInProgress = true;

            return zemUserService.remove(account.id, user.id).then(
                function () {
                    if (user) {
                        user.removed = true;
                        user.saved = false;
                    }
                },
                function () {
                    return $q.reject();
                }
            ).finally(function () {
                user.requestInProgress = false;
            });
        }

        function activate (user) {
            user.requestInProgress = true;

            return zemAccessPermissionsEndpoint.post(account.id, user.id, 'activate').then(
                function () {
                    user.saved = true;
                    user.emailResent = true;
                },
                function () {
                    user.saved = false;
                    user.emailResent = false;
                    return $q.reject();
                }
            ).finally(function () {
                user.requestInProgress = false;
            });
        }

        function undo (user) {
            user.requestInProgress = true;

            return zemUserService.create(account.id, {email: user.email}).then(
                function () {
                    user.removed = false;
                },
                function () {
                    return $q.reject();
                }
            ).finally(function () {
                user.requestInProgress = false;
            });
        }

        function promote (user) {
            user.requestInProgress = true;

            return zemAccessPermissionsEndpoint.post(account.id, user.id, 'promote').then(
                function () {
                    user.is_agency_manager = true;
                },
                function () {
                    return $q.reject();
                }
            ).finally(function () {
                user.requestInProgress = false;
            });
        }

        function downgrade (user) {
            user.requestInProgress = true;

            return zemAccessPermissionsEndpoint.post(account.id, user.id, 'downgrade').then(
                function () {
                    user.is_agency_manager = false;
                },
                function () {
                    return $q.reject();
                }
            ).finally(function () {
                user.requestInProgress = false;
            });
        }

        function getUser (userId) {
            return state.users.filter(function (user) { return user.id === userId; })[0];
        }
    }

    return {
        getInstance: function (account) {
            return new StateService(account);
        }
    };
});
