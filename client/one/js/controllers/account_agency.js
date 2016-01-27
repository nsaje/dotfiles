/* globals oneApp */
oneApp.controller('AccountAgencyCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.settings = {};
    $scope.settings.allowedSources = {};
    $scope.history = [];
    $scope.canArchive = false;
    $scope.canRestore = true;
    $scope.accountManagers = [];
    $scope.salesReps = [];
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

    $scope.mediaSourcesOrderByProp = 'name';
    $scope.selectedMediaSouces = {allowed:[], available:[]};

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
        angular.forEach($scope.selectedMediaSouces.available, function (value, _) {
            $scope.settings.allowedSources[value].allowed = true;
        });
        $scope.selectedMediaSouces.allowed.length = 0;
        $scope.selectedMediaSouces.available.length = 0;
    };

    $scope.removeFromAllowedMediaSources = function () {
        angular.forEach($scope.selectedMediaSouces.allowed, function (value, _) {
            $scope.settings.allowedSources[value].allowed = false;
        });
        $scope.selectedMediaSouces.available.length = 0;
        $scope.selectedMediaSouces.allowed.length = 0;
    };

    $scope.getServiceFees = function (search) {
        // use fresh instance because we modify the collection on the fly
        var fees = ['15', '20', '25'];

        // adds the searched for value to the array
        if (search && fees.indexOf(search) === -1) {
            fees.unshift(search);
        }

        return fees;
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
                $scope.history = data.history;
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
            },
            function (data) {
                user.saved = false;
                user.emailResent = false;
            }
        ).finally(function () {
            user.requestInProgress = false;
            $scope.getSettings(); // updates history
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

    $scope.getName = function (user) {
        return user.name;
    };
}]);
