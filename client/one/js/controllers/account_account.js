/*globals oneApp,constants,options,moment*/
oneApp.controller('AccountAccountCtrl', ['$scope', '$state', '$q', 'api', 'zemNavigationService', function ($scope, $state, $q, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.canEditAccount = false;
    $scope.salesReps = [];
    $scope.settings = {};
    $scope.settings.allowedSources = {};
    $scope.saved = false;
    $scope.errors = {};
    $scope.requestInProgress = false;
    $scope.mediaSourcesOrderByProp = 'name';
    $scope.accountTypes = options.accountTypes;
    $scope.selectedMediaSources = {
        allowed: [],
        available: [],
    };
    $scope.users = null;
    $scope.addUserRequestInProgress = false;
    $scope.addUserData = {};
    $scope.addUserErrors = null;
    $scope.canArchive = false;
    $scope.canRestore = true;

    $scope.getAllowedMediaSources = function () {
        var list = [];
        angular.forEach($scope.settings.allowedSources, function (value, key) {
            if (value.allowed) {
                value.value = key;
                this.push(value);
            }
        }, list);
        return list;
    };

    $scope.getAvailableMediaSources = function () {
        var list = [];
        angular.forEach($scope.settings.allowedSources, function (value, key) {
            if (!value.allowed) {
                value.value = key;
                this.push(value);
            }
        }, list);
        return list;
    };

    $scope.addToAllowedMediaSources =  function () {
        angular.forEach($scope.selectedMediaSources.available, function (value, _) {
            $scope.settings.allowedSources[value].allowed = true;
        });
        $scope.selectedMediaSources.allowed.length = 0;
        $scope.selectedMediaSources.available.length = 0;
    };

    $scope.removeFromAllowedMediaSources = function () {
        angular.forEach($scope.selectedMediaSources.allowed, function (value, _) {
            $scope.settings.allowedSources[value].allowed = false;
        });
        $scope.selectedMediaSources.available.length = 0;
        $scope.selectedMediaSources.allowed.length = 0;
    };

    $scope.userActionChange = function (action, userId) {
        if (action === '') {
            return;
        }

        var usr = getUser(userId);
        if (action === 'remove') {
            $scope.removeUser(userId);
        } else if (action === 'resend') {
            $scope.resendActivationMail(userId);
        }

        usr.action = null;
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

    $scope.getSettings = function (discarded) {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;
        $scope.errors = {};
        api.accountAgency.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                if (discarded) {
                    $scope.discarded = true;
                } else {
                    $scope.accountManagers = data.accountManagers;
                    $scope.salesReps = data.salesReps;
                }
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
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                zemNavigationService.updateAccountCache($state.params.id, {name: data.settings.name});
                $scope.saved = true;
            },
            function (data) {
                $scope.errors = data;
                $scope.settings.allowedSources = data.allowedSourcesData;
                $scope.saved = false;
            }
        ).finally(function () {
            $scope.requestInProgress = false;
        });
    };

    $scope.refreshPage = function () {
        zemNavigationService.reload();
        $scope.getSettings();
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
                $scope.getSettings();
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

                $scope.getSettings();
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
            },
            function (data) {
                user.saved = false;
                user.emailResent = false;
            }
        ).finally(function () {
            user.requestInProgress = false;
            $scope.getSettings();
        });
    };

    $scope.undoRemove = function (userId) {
        var user = getUser(userId);
        user.requestInProgress = true;

        api.accountUsers.put($state.params.id, {email: user.email}).then(
            function (data) {
                user.removed = false;
                $scope.getSettings();
            }
        ).finally(function () {
            user.requestInProgress = false;
        });
    };

    $scope.getName = function (user) {
        return user.name;
    };

    $scope.init = function () {
        $scope.getSettings();
        if ($scope.hasPermission('zemauth.account_agency_access_permissions')) {
            $scope.getUsers();
        }
    };

    $scope.init();
}]);
