angular
    .module('one.services')
    .service('zemUserService', function(zemPubSubService, zemUserEndpoint) {
        var pubsub = zemPubSubService.createInstance();
        var EVENTS = {
            ON_USER_CREATED: 'zem-user-created',
            ON_USER_REMOVED: 'zem-user-removed',
        };

        //
        // Public API
        //
        this.list = list;
        this.create = create;
        this.remove = remove;

        this.onUserCreated = onUserCreated;
        this.onUserRemoved = onUserRemoved;

        function list(accountId) {
            return zemUserEndpoint.list(accountId);
        }

        function create(accountId, user) {
            return zemUserEndpoint.create(accountId, user).then(function(data) {
                pubsub.notify(EVENTS.ON_USER_CREATED, {
                    accountId: accountId,
                    user: data.user,
                });
                return data;
            });
        }

        function remove(accountId, userId, fromAllAccounts) {
            return zemUserEndpoint
                .remove(accountId, userId, fromAllAccounts)
                .then(function(data) {
                    pubsub.notify(EVENTS.ON_USER_REMOVED, {
                        accountId: accountId,
                        userId: userId,
                    });
                    return data;
                });
        }

        //
        // Listener functionality
        //

        function onUserCreated(callback) {
            return pubsub.register(EVENTS.ON_USER_CREATED, callback);
        }

        function onUserRemoved(callback) {
            return pubsub.register(EVENTS.ON_USER_REMOVED, callback);
        }
    });
