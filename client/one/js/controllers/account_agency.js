/*globals oneApp*/
oneApp.controller('AccountAgencyCtrl', ['$scope', '$state', 'api', function ($scope, $state, api) {
    $scope.settings = {};
    $scope.history = [];
    $scope.canArchive = false;
    $scope.canRestore = true;
    $scope.errors = {};
    $scope.requestInProgress = false;
    $scope.saved = null;
    $scope.discarded = null;
    $scope.orderField = 'datetime';
    $scope.orderReverse = true;
    $scope.users = null;
    $scope.addUserRequestInProgress = false;
    $scope.addUserData = {};
    $scope.addUserErrors = null;

    $scope.userActionChange = function (action, userId) {
        if (action == '') {
            return;
        }

        var usr = getUser(userId);
        if (action == 'remove') {
            $scope.removeUser(userId);
        } else if (action == 'resend') {
            $scope.resendActivationMail(userId);
        }

        usr.action = null;
    }

    $scope.getSettings = function (discarded) {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;
        $scope.errors = {};
        api.accountAgency.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.discarded = discarded;
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.saveSettings = function () {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;

        api.accountAgency.save($scope.settings).then(
            function (data) {
                $scope.errors = {};
                $scope.settings = data.settings;
                $scope.history = data.history;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                $scope.updateAccounts(data.settings.name);
                $scope.updateBreadcrumbAndTitle();
                $scope.saved = true;
            },
            function (data) {
                $scope.errors = data;
                $scope.saved = false;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };
    
    $scope.refreshPage = function () {
        api.navData.list().then(function (accounts) {
            $scope.refreshNavData(accounts);
            $scope.getAccount();
        });
        $scope.getSettings();
    };

    $scope.archiveAccount = function () {
        if ($scope.canArchive) {
            api.accountArchive.archive($scope.account.id).then(function () {
                $scope.refreshPage();
            });
        }
    };

    $scope.restoreAccount = function () {
        if ($scope.canRestore) {
            api.accountArchive.restore($scope.account.id).then(function () {
                $scope.refreshPage();
            });
        }
    };

    var getUser = function (userId) {
        var result;
        $scope.users.forEach(function (user, index) {
            if (user.id === userId) {
                result = user;
            }
        });

        return result;
    };

    $scope.getUsers = function () {
        api.accountUsers.list($state.params.id).then(
            function (data) {
                $scope.users = data.users;
                $scope.users.forEach(function (user, index) {
                    user.action = null;
                    user.emailResent = false;
                });
            }
        );
    };

    $scope.addUser = function () {
        $scope.addUserRequestInProgress = true;

        api.accountUsers.put($state.params.id, $scope.addUserData).then(
            function (data) {
                var user = getUser(data.user.id);

                if (!user) {
                    user = data.user;
                    $scope.users.push(user);
                } else {
                    user.name = data.user.name;
                }

                user.saved = true;
                user.removed = false;
                user.emailSent = data.created;
                user.action = null;
                $scope.addUserErrors = null;
                $scope.addUserData = {};
                $scope.getSettings(); // updates history
            },
            function (data) {
                $scope.addUserErrors = data;
            }
        ).finally(function () {
            $scope.addUserRequestInProgress = false;
        });
    };

    $scope.removeUser = function (userId) {
        var user = getUser(userId);
        user.requestInProgress = true;

        api.accountUsers.remove($state.params.id, userId).then(
            function (userId) {
                if (user) {
                    user.removed = true;
                    user.saved = false;
                }

                $scope.getSettings(); // updates history
            }
        ).finally(function () {
            user.requestInProgress = false;
        });
    };

    $scope.resendActivationMail = function (userId) {
        var user = getUser(userId);
        user.requestInProgress = true;

        api.userActivation.post($state.params.id, userId).then(
            function (userId) {
                user.saved = true;
                user.emailResent = true;
                $scope.getSettings(); // updates history
            }
        ).finally(function () {
            user.requestInProgress = false;
        });
    };

    $scope.undoRemove = function (userId) {
        var user = getUser(userId);
        user.requestInProgress = true;

        api.accountUsers.put($state.params.id, {email: user.email}).then(
            function (data) {
                user.removed = false;
                $scope.getSettings(); // updates history
            }
        ).finally(function () {
            user.requestInProgress = false;
        });
    };

    $scope.getSettings();

    if ($scope.hasPermission('zemauth.account_agency_access_permissions')) {
        $scope.getUsers();
    }
}]);
