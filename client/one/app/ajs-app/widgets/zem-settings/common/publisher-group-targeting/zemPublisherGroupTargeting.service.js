angular
    .module('one.widgets')
    .service('zemPublisherGroupTargetingService', function(
        zemPublisherGroupsEndpoint
    ) {
        // eslint-disable-line max-len

        this.getPublisherGroups = getPublisherGroups;

        function getPublisherGroups(entity) {
            var accountId = getAccountId(entity);
            if (!accountId) return;

            return zemPublisherGroupsEndpoint.list(accountId, true);
        }

        function getAccountId(entity) {
            var accountId = null;
            if (entity.type === constants.entityType.AD_GROUP) {
                accountId = entity.parent.parent.id;
            } else if (entity.type === constants.entityType.CAMPAIGN) {
                accountId = entity.parent.id;
            } else if (entity.type === constants.entityType.ACCOUNT) {
                accountId = entity.id;
            }

            return accountId;
        }
    });
