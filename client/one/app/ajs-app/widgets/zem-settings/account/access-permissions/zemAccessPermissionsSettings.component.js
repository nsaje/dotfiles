angular.module('one.widgets').component('zemAccessPermissionsSettings', {
    bindings: {
        entity: '<',
    },
    template: require('./zemAccessPermissionsSettings.component.html'),
    controller: function(
        zemAccessPermissionsSettingsEndpoint,
        $state,
        zemPermissions,
        zemUserService
    ) {
        // eslint-disable-line max-len

        // TODO: update settings after user added/removed

        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.addUserData = {};
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.addUser = addUser;
        $ctrl.userActionChange = userActionChange;
        $ctrl.undoRemove = undoRemove;
        $ctrl.promoteUser = promoteUser;
        $ctrl.downgradeUser = downgradeUser;

        $ctrl.$onInit = function() {
            loadUsers();
        };

        function loadUsers() {
            zemUserService.list($ctrl.entity.settings.id).then(function(data) {
                $ctrl.users = data.users;
                $ctrl.agencyManagers = data.agency_managers;
                $ctrl.users.forEach(function(user) {
                    user.action = null;
                    user.emailResent = false;
                });
            });
        }

        function userActionChange(action, userId) {
            var usr = getUser(userId);
            if (action === 'remove') {
                removeUser(userId);
            } else if (action === 'resend') {
                resendActivationMail(userId);
            }

            usr.action = null;
        }

        function getUser(userId) {
            var result;
            $ctrl.users.forEach(function(user) {
                if (user.id === userId) {
                    result = user;
                }
            });
            return result;
        }

        //
        // Actions - TODO: Create local service
        //

        function addUser() {
            $ctrl.addUserRequestInProgress = true;

            zemUserService
                .create($ctrl.entity.settings.id, $ctrl.addUserData)
                .then(
                    function(data) {
                        var user = getUser(data.user.id);

                        if (!user) {
                            user = data.user;
                            $ctrl.users.push(user);
                        } else {
                            user.name = data.user.name;
                        }

                        user.saved = true;
                        user.removed = false;
                        user.emailSent = data.created;
                        user.action = null;
                        $ctrl.addUserErrors = null;
                        $ctrl.addUserData = {};
                    },
                    function(data) {
                        $ctrl.addUserErrors = data;
                    }
                )
                .finally(function() {
                    $ctrl.addUserRequestInProgress = false;
                });
        }

        function removeUser(userId) {
            var user = getUser(userId);
            user.requestInProgress = true;

            zemUserService
                .remove($ctrl.entity.settings.id, userId)
                .then(function() {
                    if (user) {
                        user.removed = true;
                        user.saved = false;
                    }
                })
                .finally(function() {
                    user.requestInProgress = false;
                });
        }

        function resendActivationMail(userId) {
            var user = getUser(userId);
            user.requestInProgress = true;

            zemAccessPermissionsSettingsEndpoint
                .post($ctrl.entity.settings.id, userId, 'activate')
                .then(
                    function() {
                        user.saved = true;
                        user.emailResent = true;
                    },
                    function() {
                        user.saved = false;
                        user.emailResent = false;
                    }
                )
                .finally(function() {
                    user.requestInProgress = false;
                });
        }

        function undoRemove(userId) {
            var user = getUser(userId);
            user.requestInProgress = true;

            zemUserService
                .create($ctrl.entity.settings.id, {email: user.email})
                .then(function() {
                    user.removed = false;
                })
                .finally(function() {
                    user.requestInProgress = false;
                });
        }

        function promoteUser(user) {
            user.requestInProgress = true;

            zemAccessPermissionsSettingsEndpoint
                .post($ctrl.entity.settings.id, user.id, 'promote')
                .then(function() {
                    user.is_agency_manager = true;
                })
                .finally(function() {
                    user.requestInProgress = false;
                });
        }

        function downgradeUser(user) {
            user.requestInProgress = true;

            zemAccessPermissionsSettingsEndpoint
                .post($ctrl.entity.settings.id, user.id, 'downgrade')
                .then(function() {
                    user.is_agency_manager = false;
                })
                .finally(function() {
                    user.requestInProgress = false;
                });
        }
    },
});
