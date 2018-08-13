angular
    .module('one.services')
    .service('zemEntityActionsEndpoint', function($http, $q) {
        // eslint-disable-line max-len

        //
        // Public API
        //
        this.archive = archive;
        this.restore = restore;
        this.activate = activate;
        this.deactivate = deactivate;

        function activate(entityType, id) {
            var url = getActionUrl(entityType, id, ACTION_ACTIVATE);
            var data = {
                state: constants.settingsState.ACTIVE,
            };

            return post(url, data);
        }

        function deactivate(entityType, id) {
            var url = getActionUrl(entityType, id, ACTION_DEACTIVATE);
            var data = {
                state: constants.settingsState.INACTIVE,
            };

            return post(url, data);
        }

        function archive(entityType, id) {
            var url = getActionUrl(entityType, id, ACTION_ARCHIVE);
            return post(url);
        }

        function restore(entityType, id) {
            var url = getActionUrl(entityType, id, ACTION_RESTORE);
            return post(url);
        }

        function post(url, data, config) {
            if (!url) throw new Error('Action Not Supported: ' + url);
            data = data || {};
            config = config || {params: {}};

            var deferred = $q.defer();
            $http
                .post(url, data, config)
                .success(function(data) {
                    deferred.resolve(data);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        //
        // Urls
        //
        var ACTION_ARCHIVE = 'archive';
        var ACTION_RESTORE = 'restore';
        var ACTION_ACTIVATE = 'activate';
        var ACTION_DEACTIVATE = 'deactivate';

        var mapActionsUrls = {};
        mapActionsUrls[constants.entityType.ACCOUNT] =
            '/api/accounts/$(id)/$(action)/';
        mapActionsUrls[constants.entityType.CAMPAIGN] =
            '/api/campaigns/$(id)/$(action)/';
        mapActionsUrls[constants.entityType.AD_GROUP] =
            '/api/ad_groups/$(id)/$(action)/';

        function getActionUrl(entityType, id, action) {
            if (action === ACTION_ACTIVATE || action === ACTION_DEACTIVATE) {
                return mapActionsUrls[entityType]
                    .replace('$(id)', id)
                    .replace('$(action)', 'settings/state');
            }
            return mapActionsUrls[entityType]
                .replace('$(id)', id)
                .replace('$(action)', action);
        }
    });
