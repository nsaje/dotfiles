angular
    .module('one.views')
    .controller('zemMainView', function(
        $scope,
        $location,
        $q,
        $state,
        zemNavigationService
    ) {
        var $ctrl = this;

        initialize();

        function initialize() {
            checkStateChange();
            $scope.$on('$zemStateChangeSuccess', checkStateChange);
        }

        var checksPromise;
        function checkStateChange() {
            if (checksPromise) return;

            $ctrl.mainStateAllowed = false;
            checksPromise = $q
                .all([
                    canActivateMainState(),
                    checkRedirectToDefaultAccount(),
                    checkIfEntityExists(),
                ])
                .then(function() {
                    checksPromise = null;
                    $ctrl.mainStateAllowed = true;
                })
                .catch(function(redirect) {
                    checksPromise = null;
                    if (redirect) {
                        var options = redirect.options || {
                            reload: true,
                            location: 'replace',
                        };
                        $state.go(redirect.state, redirect.params, options);
                    }
                });
        }

        function canActivateMainState() {
            var deferred = $q.defer();
            zemNavigationService
                .getAccountsAccess()
                .then(function(accountsAccess) {
                    if (accountsAccess.hasAccounts) {
                        deferred.resolve();
                    } else {
                        deferred.reject({state: 'error.forbidden'});
                    }
                });
            return deferred.promise;
        }

        function checkRedirectToDefaultAccount() {
            if (!$state.is('v2')) return $q.resolve();

            var deferred = $q.defer();
            zemNavigationService
                .getAccountsAccess()
                .then(function(accountsAccess) {
                    if (accountsAccess.accountsCount > 1) {
                        deferred.reject({
                            state: 'v2.analytics',
                            params: {level: constants.levelStateParam.ACCOUNTS},
                        });
                    } else {
                        var defaultAccountParams = {
                            level: constants.levelStateParam.ACCOUNT,
                            id: accountsAccess.defaultAccountId,
                        };
                        deferred.reject({
                            state: 'v2.analytics',
                            params: defaultAccountParams,
                        });
                    }
                });
            return deferred.promise;
        }

        function checkIfEntityExists() {
            var entityGetter = getEntityGetter($state.params.level);
            if (!entityGetter) return $q.resolve();

            var deferred = $q.defer();
            entityGetter($state.params.id)
                .then(function() {
                    deferred.resolve();
                })
                .catch(function() {
                    deferred.reject({
                        state: 'v2.analytics',
                        params: {
                            level: constants.levelStateParam.ACCOUNTS,
                            id: null,
                        },
                    });
                });
            return deferred.promise;
        }

        function getEntityGetter(level) {
            switch (level) {
                case constants.levelStateParam.ACCOUNT:
                    return zemNavigationService.getAccount;
                case constants.levelStateParam.CAMPAIGN:
                    return zemNavigationService.getCampaign;
                case constants.levelStateParam.AD_GROUP:
                    return zemNavigationService.getAdGroup;
            }
        }
    });
