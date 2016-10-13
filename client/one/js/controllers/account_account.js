/* globals angular,constants,options,moment,$ */
angular.module('one.legacy').controller('AccountAccountCtrl', ['$scope', '$state', '$q', '$uibModal', 'api', 'zemAccountService', 'zemUserService', 'zemNavigationService', '$timeout', function ($scope, $state, $q, $uibModal, api, zemAccountService, zemUserService, zemNavigationService, $timeout) { // eslint-disable-line max-len

    $scope.canEditAccount = false;
    $scope.salesReps = [];
    $scope.settings = {};
    $scope.settings.allowedSources = {};
    $scope.saved = false;
    $scope.errors = {};
    $scope.constants = constants;
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
    $scope.agencyManagers = null;
    $scope.facebookPageChangedInfo = {
        changed: false
    };
    var agencies = [];

    $scope.isAnySettingSettable = function () {
        return $scope.hasPermission('zemauth.can_modify_allowed_sources') ||
            $scope.hasPermission('zemauth.can_modify_account_name') ||
            $scope.hasPermission('zemauth.can_modify_facebook_page') ||
            $scope.hasPermission('zemauth.can_modify_account_type') ||
            $scope.hasPermission('zemauth.can_set_account_sales_representative') ||
            $scope.hasPermission('zemauth.can_modify_account_manager');
    };

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
            zemAccountService.archive($scope.account.id).then(function () {
                $scope.refreshPage();
            });
        }
    };

    $scope.restoreAccount = function () {
        if ($scope.canRestore) {
            zemAccountService.restore($scope.account.id).then(function () {
                $scope.refreshPage();
            });
        }
    };

    $scope.getSettings = function (discarded) {
        $scope.saved = null;
        $scope.discarded = null;
        $scope.requestInProgress = true;
        $scope.errors = {};
        $scope.facebookPageChangedInfo.changed = false;
        zemAccountService.get($state.params.id).then(
            function (data) {
                $scope.settings = data.settings;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                if (discarded) {
                    $scope.discarded = true;
                } else {
                    $scope.accountManagers = data.accountManagers;
                    $scope.salesReps = data.salesReps;
                    agencies = data.agencies;
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

        if ($scope.facebookPageChangedInfo.changed) {
            var facebookPageChangedModalInstance = $uibModal.open({
                templateUrl: '/partials/facebook_page_changed_modal.html',
                controller: ['$scope', function ($scope) {
                    $scope.ok = function () {
                        $scope.$close();
                    };

                    $scope.cancel = function () {
                        $scope.$dismiss('cancel');
                    };
                }],
                size: 'lg',
            });
            facebookPageChangedModalInstance.result.then(function () {
                executeSaveSettings();
            }, function () {
                $scope.getSettings(true);
            });
        } else {
            executeSaveSettings();
        }
    };

    function executeSaveSettings () {
        $scope.requestInProgress = true;
        var updateData = {settings: $scope.settings};
        zemAccountService.update($scope.settings.id, updateData).then(
            function (data) {
                $scope.errors = {};
                $scope.settings = data.settings;
                $scope.canArchive = data.canArchive;
                $scope.canRestore = data.canRestore;
                agencies = data.agencies;
                $scope.checkFacebookAccountStatus();
                zemNavigationService.updateAccountCache($state.params.id, {
                    name: data.settings.name,
                    agency: data.settings.agency.id || null,
                });
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
    }

    $scope.checkFacebookAccountStatus = function () {
        var facebookPage = $scope.settings.facebookPage;
        var facebookStatus = $scope.settings.facebookStatus;
        if (facebookPage === null || facebookStatus !== constants.facebookStatus.PENDING) {
            return;
        }
        zemAccountService.getFacebookAccountStatus($scope.settings.id).then(
            function (data) {
                var facebookAccountStatus = data.data.status;
                $scope.settings.facebookStatus = facebookAccountStatus;
            },
            function () {
                $scope.settings.facebookStatus = constants.facebookStatus.ERROR;
            }
        );
        if ($scope.facebookAccountStatusChecker !== null) {
            // prevent the creation of multiple Facebook account checkers (for example, when Facebook page URL is
            // updated multiple times).
            $timeout.cancel($scope.facebookAccountStatusChecker);
        }

        $scope.facebookAccountStatusChecker = $timeout($scope.checkFacebookAccountStatus, 30 * 1000);
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
        zemUserService.list($state.params.id).then(
            function (data) {
                $scope.users = data.users;
                $scope.agencyManagers = data.agency_managers;
                $scope.users.forEach(function (user, index) {
                    user.action = null;
                    user.emailResent = false;
                });
            }
        );
    };

    $scope.addUser = function () {
        $scope.addUserRequestInProgress = true;

        zemUserService.create($state.params.id, $scope.addUserData).then(
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

        zemUserService.remove($state.params.id, userId).then(
            function () {
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

        api.accountUserAction.post($state.params.id, userId, 'activate').then(
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

        zemUserService.create($state.params.id, {email: user.email}).then(
            function (data) {
                user.removed = false;
                $scope.getSettings();
            }
        ).finally(function () {
            user.requestInProgress = false;
        });
    };

    $scope.promoteUser = function (user) {
        user.requestInProgress = true;

        api.accountUserAction.post($scope.account.id, user.id, 'promote').then(
            function (data) {
                user.is_agency_manager = true;
            }
        ).finally(function () {
            user.requestInProgress = false;
        });
    };

    $scope.downgradeUser = function (user) {
        user.requestInProgress = true;

        api.accountUserAction.post($scope.account.id, user.id, 'downgrade').then(
            function (data) {
                user.is_agency_manager = false;
            }
        ).finally(function () {
            user.requestInProgress = false;
        });
    };

    $scope.getName = function (user) {
        return user.name;
    };

    var convertSelect2 = function (obj) {
        return {
            id: obj.name,
            text: obj.name,
            obj: obj,
        };
    };

    $scope.agencySelect2Config = {
        dropdownCssClass: 'service-fee-select2',
        createSearchChoice: function (term, data) {
            if ($(data).filter(function () {
                return this.text.localeCompare(term) === 0;
            }).length === 0) {
                return {id: term, text: term + ' (Create new agency)'};
            }
        },
        data: function () {
            return {
                results: agencies.map(convertSelect2),
            };
        },
    };

    $scope.updateAgencyDefaults = function () {
        if ($scope.settings.agency && $scope.settings.agency.obj) {
            if ($scope.settings.accountType == constants.accountTypes.UNKNOWN) {
                $scope.settings.accountType = $scope.settings.agency.obj.defaultAccountType;
            }
            if (!$scope.settings.defaultSalesRepresentative) {
                $scope.settings.defaultSalesRepresentative = $scope.settings.agency.obj.salesRepresentative.toString();
            }
        }
    };

    $scope.init = function () {
        $scope.getSettings();
        if ($scope.hasPermission('zemauth.account_agency_access_permissions')) {
            $scope.getUsers();
        }
        $scope.setActiveTab();
    };

    $scope.init();
}]);
