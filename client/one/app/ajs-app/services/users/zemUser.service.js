angular
    .module('one.services')
    .service('zemUserService', function(zemPubSubService, zemUserEndpoint) {
        var currentUser = null;
        var pubsub = zemPubSubService.createInstance();
        var EVENTS = {
            ON_USER_CREATED: 'zem-user-created',
            ON_USER_REMOVED: 'zem-user-removed',
            ON_CURRENT_USER_UPDATED: 'zem-user-current-updated',
        };

        //
        // Public API
        //
        this.init = init;
        this.list = list;
        this.create = create;
        this.remove = remove;
        this.get = get;
        this.current = current;

        this.onUserCreated = onUserCreated;
        this.onUserRemoved = onUserRemoved;
        this.onCurrentUserUpdated = onCurrentUserUpdated;

        //
        // Internal
        //
        function init() {
            return zemUserEndpoint.get('current').then(function(user) {
                currentUser = user;
                pubsub.notify(EVENTS.ON_CURRENT_USER_UPDATED, user);
                // Configure Raven/Sentry user context
                window.Raven.setUserContext({
                    username: user.name,
                    email: user.email,
                });
            });
        }

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

        function get(id) {
            return zemUserEndpoint.get(id);
        }

        function current() {
            return currentUser;
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

        function onCurrentUserUpdated(callback) {
            return pubsub.register(EVENTS.ON_CURRENT_USER_UPDATED, callback);
        }
    });
