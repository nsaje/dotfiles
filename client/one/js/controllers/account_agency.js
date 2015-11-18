/*globals oneApp*/
oneApp.controller('AccountAgencyCtrl', ['$scope', '$state', '$modal', 'api', 'zemFilterService', function ($scope, $state, $modal, api, zemFilterService) {
    $scope.settings = {};
    $scope.settings.allowedSources = {};
    $scope.history = [];
    $scope.conversionPixels = [];
    $scope.canArchive = false;
    $scope.canRestore = true;
    $scope.accountManagers = [];
    $scope.salesReps = [];
    $scope.errors = {};
    $scope.requestInProgress = false;
    $scope.listPixelsInProgress = false;
    $scope.listPixelsError = false;
    $scope.saved = null;
    $scope.discarded = null;
    $scope.orderField = 'datetime';
    $scope.orderReverse = true;
    $scope.pixelOrderField = 'slug';
    $scope.pixelOrderReverse = false;
    $scope.users = null;
    $scope.addUserRequestInProgress = false;
    $scope.addUserData = {};
    $scope.addUserErrors = null;
    $scope.conversionPixelTagPrefix = '';

    $scope.mediaSourcesOrderByProp = 'value';
    $scope.selectedMediaSouces = {allowed:[], available:[]};

    $scope.getAllowedMediaSources = function () {
        var list = [];
        angular.forEach($scope.settings.allowedSources, function(value, key) {
            if(value.allowed){
                value.value = key;
                this.push(value);
            }
        }, list);
        return list;
    };

    $scope.getAvailableMediaSources = function () {
        var list = [];
        angular.forEach($scope.settings.allowedSources, function(value, key) {
            if(!value.allowed){
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

    $scope.getServiceFees = function(search) {
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
                $scope.mediaSourcesData = $scope.settings.allowedSources;
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

    $scope.getConversionPixels = function () {
        $scope.listPixelsInProgress = true;
        api.conversionPixel.list($scope.account.id).then(
            function (data) {
                $scope.conversionPixels = data.rows;
                $scope.conversionPixelTagPrefix = data.conversionPixelTagPrefix;
            },
            function (data) {
                $scope.listPixelsError = true;
            }
        ).finally(function () {
            $scope.listPixelsInProgress = false;
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

    $scope.addConversionPixel = function () {
        var modalInstance = $modal.open({
            templateUrl: '/partials/add_conversion_pixel_modal.html',
            controller: 'AddConversionPixelModalCtrl',
            windowClass: 'modal',
            scope: $scope
        });

        modalInstance.result.then(function(conversionPixel) {
            $scope.conversionPixels.push(conversionPixel);
            $scope.getSettings();
        });

        return modalInstance;
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

    $scope.archiveConversionPixel = function (conversionPixel) {
        conversionPixel.requestInProgress = true;
        conversionPixel.error = false;
        api.conversionPixel.archive(conversionPixel.id).then(
            function (data) {
                conversionPixel.archived = data.archived;
                $scope.getSettings();
            },
            function (data) {
                conversionPixel.error = true;
            }
        ).finally(function () {
            conversionPixel.requestInProgress = false;
        });
    };

    $scope.restoreConversionPixel = function (conversionPixel) {
        conversionPixel.requestInProgress = true;
        conversionPixel.error = false;
        api.conversionPixel.restore(conversionPixel.id).then(
            function (data) {
                conversionPixel.archived = data.archived;
                $scope.getSettings();
            },
            function (data) {
                conversionPixel.error = true;
            }
        ).finally(function () {
            conversionPixel.requestInProgress = false;
        });
    };

    $scope.copyConversionPixelTag = function (conversionPixel) {
        var scope = $scope.$new(true);
        scope.conversionPixelTag = $scope.getConversionPixelTag(conversionPixel.url);

        var modalInstance = $modal.open({
            templateUrl: '/partials/copy_conversion_pixel_modal.html',
            windowClass: 'modal',
            scope: scope
        });

        return modalInstance;
    };

    $scope.filterConversionPixels = function (conversionPixel) {
        if (zemFilterService.getShowArchived()) {
            return true;
        }

        return !conversionPixel.archived;
    };

    $scope.getSettings();
    $scope.getConversionPixels();

    if ($scope.hasPermission('zemauth.account_agency_access_permissions')) {
        $scope.getUsers();
    }

    $scope.getName = function (user) {
        return user.name;
    };
}]);
