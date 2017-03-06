angular.module('one.services').service('zemStateGuardService', function ($rootScope, $injector, $q, $state, zemUserService, zemNavigationService, zemPermissions) { // eslint-disable-line max-len
    this.init = init;
    this.checkPermission = checkPermission;
    this.canActivateMainState = canActivateMainState;

    function init () {
        $rootScope.$on('$stateChangeStart', checkStateChange);
    }

    var stateChangeChecked = false;
    function checkStateChange (event, toState, toParams) {
        // NOTE: When navigating to states with state guard checks, this function is called twice. The first time
        // navigation is stopped by event.preventDefault() and after all checks resolve, navigation is triggered again
        // by $state.go(). 'stateChangeChecked' variable is used to know whether navigation to state is allowed on the
        // second function call (after checks are executed).
        if (stateChangeChecked) {
            stateChangeChecked = false;
            return;
        }

        var checks = getStateGuardChecks(toState);
        if (checks.length === 0) return;

        event.preventDefault();

        $q.all(checks)
            .then(function () {
                stateChangeChecked = true;
                $state.go(toState, toParams);
            })
            .catch(function (error) {
                if (error) {
                    $state.go(error.state, error.params);
                }
            });
    }

    function getStateGuardChecks (state) {
        // Find all 'canActivate' properties in state and its parent states and return an array of all checks defined
        var checks = [];
        var stateData = state.data;
        while (stateData) {
            if (stateData.hasOwnProperty('canActivate')) {
                var currentChecks = $injector.invoke(stateData.canActivate);
                checks = checks.concat(currentChecks);
            }
            stateData = Object.getPrototypeOf(stateData);
        }
        return checks;
    }

    function checkPermission (permission) {
        // If zemUserService has user's data cached we can immediately check permission
        if (zemUserService.current()) {
            return zemPermissions.hasPermission(permission) ? $q.resolve() : $q.reject({state: 'error.forbidden'});
        }

        // If zemUserService doesn't have user's data cached we wait for it to load and then check permission
        var deferred = $q.defer();
        var handler = zemUserService.onCurrentUserUpdated(function () {
            if (zemPermissions.hasPermission(permission)) {
                deferred.resolve();
            } else {
                deferred.reject({state: 'error.forbidden'});
            }
            handler();
        });
        return deferred.promise;
    }

    function canActivateMainState () {
        var deferred = $q.defer();
        zemNavigationService.getAccountsAccess()
            .then(function (accountsAccess) {
                if (accountsAccess.hasAccounts) {
                    deferred.resolve();
                } else {
                    deferred.reject({state: 'error.forbidden'});
                }
            });
        return deferred.promise;
    }
});
