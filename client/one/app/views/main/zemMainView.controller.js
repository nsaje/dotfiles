angular.module('one.views').controller('zemMainView', function ($scope, $q, $state, zemPermissions, zemNavigationService) { // eslint-disable-line max-len
    var $ctrl = this;

    initialize();

    function initialize () {
        $ctrl.hasPermission = zemPermissions.hasPermission;

        checkStateChange();
        $scope.$on('$stateChangeSuccess', checkStateChange);
    }

    var checksPromise;
    function checkStateChange () {
        if (checksPromise) return;

        $ctrl.mainStateAllowed = false;

        checksPromise = $q.all([canActivateMainState()])
            .then(function () {
                checksPromise = null;
                $ctrl.mainStateAllowed = true;
            })
            .catch(function (error) {
                checksPromise = null;
                if (error) {
                    $state.go(error.state, error.params, {reload: true, location: 'replace'});
                }
            });
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
