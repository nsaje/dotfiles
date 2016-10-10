angular.module('one.services').service('zemAccountService', ['$http', '$q', 'zemEntityInstanceService', 'zemEntityActionsService', function ($http, $q, zemEntityInstanceService, zemEntityActionsService) { // eslint-disable-line max-len

    var entityInstanceService = zemEntityInstanceService.createInstance(constants.entityType.ACCOUNT);
    var entityActionsService = zemEntityActionsService.createInstance(constants.entityType.ACCOUNT);

    //
    // Public API
    //
    this.get = entityInstanceService.get;
    this.update = entityInstanceService.update;
    this.create = entityInstanceService.create;

    this.archive = entityActionsService.archive;
    this.restore = entityActionsService.restore;
    this.archiveAccounts = entityActionsService.archiveEntities;
    this.restoreAccounts = entityActionsService.restoreEntities;

    this.getAction = entityActionsService.getAction;
    this.onAccountCreated = entityInstanceService.onEntityCreated;
    this.onAccountUpdated = entityInstanceService.onEntityUpdated;
    this.onAccountActionExecuted = entityActionsService.onActionExecuted;

    // TODO: refactor (new service?)
    this.getFacebookAccountStatus = getFacebookAccountStatus;

    function getFacebookAccountStatus (accountId) {
        var deferred = $q.defer();
        var url = '/api/accounts/' + accountId + '/facebook_account_status/';

        $http.get(url).
            success(function (data) {
                deferred.resolve(data);
            }).
            error(function (data) {
                deferred.reject(data);
            });

        return deferred.promise;
    }
}]);
