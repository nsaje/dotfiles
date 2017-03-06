angular.module('one.widgets').service('zemPublisherGroupTargetingService', function (zemPublisherGroupsEndpoint) { // eslint-disable-line max-len

    this.getPublisherGroups = getPublisherGroups;

    function getPublisherGroups (entity) {
        var accountId = getAccountId(entity);
        if (!accountId) return;

        return zemPublisherGroupsEndpoint.list(accountId, true);
    }

    function getAccountId (entity) {
        var accountId = null;
        if (entity.type === 'adGroup') {
            accountId = entity.parent.parent.id;
        } else if (entity.type === 'campaign') {
            accountId = entity.parent.id;
        } else if (entity.type === 'account') {
            accountId = entity.id;
        }

        return accountId;
    }
});
